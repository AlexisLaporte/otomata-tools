"""
Pappers Client - Browser automation for French company data from pappers.fr

Inherits from BrowserClient for browser management.
"""

import re
from typing import Optional, Dict, Any, List

from .lib.browser_client import BrowserClient
from ...config import get_secret


class PappersClient(BrowserClient):
    """
    Pappers.fr scraping client for French company legal data.

    Features:
    - Company lookup by SIREN
    - Company search
    - Director/executive extraction
    - Financial data extraction
    - Establishment (établissement) data
    """

    BASE_URL = "https://www.pappers.fr"
    API_URL = "https://api.pappers.fr/v2/entreprise"

    def __init__(self, headless: bool = True, api_key: str = None):
        """
        Initialize Pappers client.

        Args:
            headless: Run browser in headless mode
            api_key: Pappers API key (optional, for URL resolution)
        """
        super().__init__(
            headless=headless,
            locale="fr-FR",
            timezone_id="Europe/Paris",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        )

        self.api_key = api_key or get_secret("PAPPERS_API_KEY")
        self._cartographie_data = None

    async def start(self):
        """Start browser and setup response interception."""
        await super().start()

        # Intercept cartographie API responses
        async def handle_cartographie(response):
            url = response.url
            if "cartographie" in url.lower() and response.status == 200:
                try:
                    self._cartographie_data = await response.json()
                except:
                    pass

        self.on_response(handle_cartographie)
        return self

    async def _wait_for_cloudflare(self, max_wait: int = 15) -> bool:
        """Wait for Cloudflare challenge to resolve."""
        for _ in range(max_wait):
            title = await self.page.title()
            if "just a moment" not in title.lower():
                return True
            await self.wait(1)
        return False

    def _get_company_url_from_api(self, siren: str) -> Optional[str]:
        """Use Pappers API to get company URL."""
        if not self.api_key:
            return None

        import urllib.request
        import json

        try:
            url = f"{self.API_URL}?siren={siren}&api_token={self.api_key}"
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode())
                nom = data.get("nom_entreprise", "")
                if nom:
                    slug = nom.lower()
                    slug = re.sub(r"[^\w\s-]", "", slug)
                    slug = re.sub(r"[\s_]+", "-", slug)
                    slug = slug.strip("-")
                    return f"{self.BASE_URL}/entreprise/{slug}-{siren}"
        except Exception as e:
            print(f"API lookup failed: {e}")

        return None

    async def get_company_by_siren(self, siren: str) -> Dict[str, Any]:
        """
        Get company data by SIREN number.

        Args:
            siren: 9-digit SIREN number

        Returns:
            Dict with company data
        """
        siren = re.sub(r"\s", "", siren)

        # Try simple URL first
        simple_url = f"{self.BASE_URL}/entreprise/{siren}"
        await self.goto(simple_url)
        await self._wait_for_cloudflare()
        await self.wait(1)

        current_url = self.page.url

        if "/entreprise/" in current_url and siren in current_url:
            return await self._extract_company_data(siren)

        # Fallback: try API
        company_url = self._get_company_url_from_api(siren)
        if company_url:
            return await self.get_company_by_url(company_url)

        return {"error": f"Company not found for SIREN {siren}", "siren": siren}

    async def get_company_by_url(self, url: str) -> Dict[str, Any]:
        """Get company data from direct Pappers URL."""
        await self.goto(url)
        await self._wait_for_cloudflare()
        await self.wait(1)

        siren_match = re.search(r"(\d{9})$", url)
        siren = siren_match.group(1) if siren_match else None

        return await self._extract_company_data(siren)

    async def _extract_company_data(self, siren: Optional[str] = None) -> Dict[str, Any]:
        """Extract all company data from current page."""
        data = {
            "siren": siren,
            "url": self.page.url,
            "identite": {},
            "dirigeants": [],
            "finances": {},
            "etablissements": [],
            "relations": [],
        }

        try:
            # Company name
            name_el = await self.query_selector("h1, .company-name")
            if name_el:
                data["identite"]["nom"] = await name_el.inner_text()

            await self._extract_identity_section(data)
            await self._extract_dirigeants(data)
            await self._extract_finances(data)
            await self._extract_etablissements(data)

        except Exception as e:
            data["error"] = str(e)

        return data

    async def _extract_identity_section(self, data: Dict) -> None:
        """Extract identity/legal info section."""
        identite = await self.evaluate('''
            () => {
                const info = {};
                const cardText = document.body.textContent;

                const sirenMatch = cardText.match(/SIREN\\s*:?\\s*(\\d{3}\\s*\\d{3}\\s*\\d{3})/i);
                if (sirenMatch) info.siren = sirenMatch[1].trim();

                const siretMatch = cardText.match(/SIRET\\s*:?\\s*(\\d{3}\\s*\\d{3}\\s*\\d{3}\\s*\\d{5})/i);
                if (siretMatch) info.siret = siretMatch[1].trim();

                const formeMatch = cardText.match(/Forme juridique\\s*:?\\s*([^\\n]+)/i);
                if (formeMatch) info.forme_juridique = formeMatch[1].trim();

                const capitalMatch = cardText.match(/Capital\\s*:?\\s*([^\\n]+)/i);
                if (capitalMatch) info.capital = capitalMatch[1].trim();

                const effectifMatch = cardText.match(/Effectif\\s*:?\\s*([^\\n]+)/i);
                if (effectifMatch) info.effectif = effectifMatch[1].trim();

                return info;
            }
        ''')

        data["identite"].update(identite)

    async def _extract_dirigeants(self, data: Dict) -> None:
        """Extract company executives/directors."""
        dirigeants_list = await self.evaluate('''
            () => {
                const dirigeants = [];
                const section = document.querySelector('section#dirigeants, section[data-id="dirigeants"]');
                if (!section) return [];

                const firstUl = section.querySelector('ul');
                if (!firstUl) return [];

                const items = firstUl.querySelectorAll('li.dirigeant:not(.ancien)');

                for (const item of items) {
                    const nomEl = item.querySelector('.nom a') || item.querySelector('.nom');
                    const qualiteEl = item.querySelector('.qualite');

                    if (nomEl && qualiteEl) {
                        dirigeants.push({
                            nom: nomEl.textContent.trim(),
                            fonction: qualiteEl.textContent.trim()
                        });
                    }
                }

                return dirigeants;
            }
        ''')

        data["dirigeants"] = dirigeants_list

    async def _extract_finances(self, data: Dict) -> None:
        """Extract financial data."""
        finances = await self.evaluate('''
            () => {
                const metrics = {};
                const section = document.querySelector('section#finances, section[data-id="finances"]');
                if (!section) return metrics;

                const rows = section.querySelectorAll('tr, .finance-row');
                for (const row of rows) {
                    const labelEl = row.querySelector('th, .label');
                    const valueEl = row.querySelector('td, .value');
                    if (labelEl && valueEl) {
                        const label = labelEl.textContent.trim().toLowerCase();
                        const value = valueEl.textContent.trim();

                        if (label.includes('chiffre') && label.includes('affaires')) {
                            metrics.chiffre_affaires = value;
                        } else if (label.includes('résultat')) {
                            metrics.resultat = value;
                        } else if (label.includes('effectif')) {
                            metrics.effectif = value;
                        }
                    }
                }

                return metrics;
            }
        ''')

        data["finances"] = finances

    async def _extract_etablissements(self, data: Dict) -> None:
        """Extract company establishments."""
        etablissements = await self.evaluate('''
            () => {
                const etabs = [];
                const section = document.querySelector('section#etablissements');
                if (!section) return etabs;

                const items = section.querySelectorAll('.etablissement, li');
                const seen = new Set();

                for (const item of items) {
                    const text = item.textContent;

                    if (text.toLowerCase().includes('fermé')) continue;
                    if (!text.includes('En activité')) continue;

                    const siretMatch = text.match(/\\b(\\d{3}\\s*\\d{3}\\s*\\d{3}\\s*\\d{5})\\b/);
                    if (!siretMatch) continue;

                    const siret = siretMatch[1].replace(/\\s/g, '');
                    if (seen.has(siret)) continue;
                    seen.add(siret);

                    let adresse = null;
                    const adresseMatch = text.match(/Adresse\\s*:?\\s*([^\\n]+?)(?=Voir|Date|$)/i);
                    if (adresseMatch) adresse = adresseMatch[1].trim();

                    etabs.push({
                        siret: siret,
                        adresse: adresse,
                        statut: 'En activité'
                    });
                }

                return etabs;
            }
        ''')

        data["etablissements"] = etablissements

    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search companies by name or keyword.

        Args:
            query: Search query
            limit: Max results to return

        Returns:
            List of company summaries
        """
        search_url = f"{self.BASE_URL}/recherche?q={query}"
        await self.goto(search_url)
        await self._wait_for_cloudflare()
        await self.wait(1)

        results = []
        seen_sirens = set()

        result_items = await self.query_selector_all('a[href*="/entreprise/"]')

        for item in result_items:
            if len(results) >= limit:
                break
            try:
                href = await item.get_attribute("href")
                text = (await item.inner_text()).strip()

                if not text or len(text) < 2:
                    continue

                siren_match = re.search(r"(\d{9})$", href or "")
                siren = siren_match.group(1) if siren_match else None

                if siren and siren in seen_sirens:
                    continue
                if siren:
                    seen_sirens.add(siren)

                results.append({
                    "nom": text.split("\n")[0].strip(),
                    "siren": siren,
                    "url": f"{self.BASE_URL}{href}" if href and not href.startswith("http") else href
                })
            except:
                continue

        return results
