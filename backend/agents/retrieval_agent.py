import json
import urllib.request
import urllib.parse
from typing import List


class RetrievalAgent:
    def __init__(self, data_path: str):
        with open(data_path, "r", encoding="utf-8") as f:
            self.papers = json.load(f)

    def search_papers(self, disease: str, use_real: bool = False) -> List[dict]:
        # 1. Try to fetch from Europe PMC live REST API if use_real is requested
        if use_real:
            try:
                query = urllib.parse.quote(f'"{disease}" AND abstract:* AND (drug OR treatment OR therapy)')
                url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={query}&format=json&resultType=core&pageSize=15"
                
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 Medical-Miniproject/1.0'})
                with urllib.request.urlopen(req, timeout=15) as response:
                    data = json.loads(response.read().decode('utf-8'))
                
                results = []
                for item in data.get('resultList', {}).get('result', []):
                    pid = item.get('pmid', item.get('id', 'Unknown'))
                    title = item.get('title', 'Unknown Title')
                    abstract = item.get('abstractText', '')
                    if not abstract:
                        continue
                    
                    paper = {
                        "id": f"PMID:{pid}",
                        "title": title,
                        "abstract": abstract,
                        "drugs": [],
                        "diseases": [disease],
                        "genes": [],
                        "url": f"https://europepmc.org/article/MED/{pid}"
                    }
                    results.append(paper)
                
                if results:
                    return results
                    
            except Exception as e:
                print(f"Europe PMC fetch failed: {e}")
                pass

        # 2. Fallback to mock data keyword search
        q = disease.lower()
        results = []
        for p in self.papers:
            text = (p.get("title", "") + " " + p.get("abstract", "")).lower()
            tags = " ".join(p.get("diseases", [])).lower()
            if q in text or q in tags:
                results.append(p)
        # Do not return fallback papers for unknown queries; return empty list so caller can handle validation
        return results
