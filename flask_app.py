import json
from flask import Flask, request, jsonify
import networkx as nx
import re

app = Flask(__name__)


class RetrievalAgent:
    def __init__(self, path="data/papers.json"):
        with open(path, "r", encoding="utf-8") as f:
            self.papers = json.load(f)

    def search_papers(self, disease: str):
        q = disease.lower()
        results = []
        for p in self.papers:
            text = (p.get("title", "") + " " + p.get("abstract", "")).lower()
            tags = " ".join(p.get("diseases", [])).lower()
            if q in text or q in tags:
                results.append(p)
        if not results:
            # return first 3 as fallback
            return self.papers[:3]
        return results


class ExtractionAgent:
    def extract(self, papers):
        drugs = set()
        diseases = set()
        genes = set()
        for p in papers:
            if p.get("drugs"):
                drugs.update(p.get("drugs"))
            if p.get("diseases"):
                diseases.update(p.get("diseases"))
            if p.get("genes"):
                genes.update(p.get("genes"))

            # fallback heuristics from abstract
            abs_text = p.get("abstract", "")
            if not (p.get("drugs") or p.get("diseases") or p.get("genes")) and abs_text:
                caps = re.findall(r"\b([A-Z][a-zA-Z0-9]{2,})\b", abs_text)
                for token in caps[:2]:
                    diseases.add(token)
                for token in caps[2:4]:
                    genes.add(token)

        return {
            "drugs": sorted(drugs),
            "diseases": sorted(diseases),
            "genes": sorted(genes),
        }


class GraphAgent:
    def build_graph(self, entities_per_paper, papers):
        G = nx.Graph()
        for p in papers:
            pid = p.get("id")
            e = p.get("drugs", []) + p.get("diseases", []) + p.get("genes", [])
            for n in e:
                if not G.has_node(n):
                    # naive typing by simple heuristics
                    ntype = "entity"
                    if n.lower().startswith("drug") or n.lower().startswith("drug"):
                        ntype = "drug"
                    elif n.lower().startswith("gene") or n.lower().startswith("gene"):
                        ntype = "gene"
                    elif n.lower().startswith("disease"):
                        ntype = "disease"
                    G.add_node(n, type=ntype)

            for i in range(len(e)):
                for j in range(i + 1, len(e)):
                    a = e[i]
                    b = e[j]
                    if G.has_edge(a, b):
                        G[a][b]["weight"] += 1
                        G[a][b]["papers"].append(pid)
                    else:
                        G.add_edge(a, b, weight=1, papers=[pid])

        return G


class PredictionAgent:
    def predict(self, G: nx.Graph, disease: str):
        preds = []
        if disease not in G:
            return preds
        disease_neighbors = set(G.neighbors(disease))
        for n, data in G.nodes(data=True):
            if data.get("type") != "drug":
                continue
            if G.has_edge(n, disease):
                continue
            drug_neighbors = set(G.neighbors(n))
            common = disease_neighbors.intersection(drug_neighbors)
            union = disease_neighbors.union(drug_neighbors)
            score = 0.0
            if union:
                score = len(common) / len(union)
            evidence = set()
            for mid in common:
                if G.has_edge(disease, mid):
                    evidence.update(G[disease][mid].get("papers", []))
                if G.has_edge(n, mid):
                    evidence.update(G[n][mid].get("papers", []))
            preds.append({"drug": n, "score": round(float(score), 3), "evidence": sorted(evidence)})
        preds = sorted(preds, key=lambda x: x["score"], reverse=True)
        return preds


@app.route("/search")
def search():
    disease = request.args.get("disease", "").strip()
    if not disease:
        return jsonify({"error": "provide disease parameter, e.g. /search?disease=Disease X"}), 400

    retriever = RetrievalAgent()
    extractor = ExtractionAgent()
    grapher = GraphAgent()
    predictor = PredictionAgent()

    papers = retriever.search_papers(disease)
    entities = extractor.extract(papers)
    G = grapher.build_graph(entities, papers)
    predictions = predictor.predict(G, disease)

    drugs = entities.get("drugs", [])
    genes = entities.get("genes", [])
    confidence_scores = [p["score"] for p in predictions]

    resp = {
        "disease": disease,
        "drugs": drugs,
        "genes": genes,
        "predictions": predictions,
        "confidence_scores": confidence_scores,
    }
    return jsonify(resp)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
