import networkx as nx
import pandas as pd
import os

class GraphAgent:
    def __init__(self, drug_gene_path="data/drug_gene.csv", gene_disease_path="data/gene_disease.csv"):
        self.dg_path = drug_gene_path
        self.gd_path = gene_disease_path
        self.G = nx.Graph()
        self.load_data()

    def load_data(self):
        if os.path.exists(self.dg_path) and os.path.exists(self.gd_path):
            df_dg = pd.read_csv(self.dg_path)
            df_gd = pd.read_csv(self.gd_path)
            
            # Build Knowledge Graph
            for _, row in df_dg.iterrows():
                u, v = row['drug'], row['gene']
                self.G.add_node(u, type="drug")
                self.G.add_node(v, type="gene")
                self.G.add_edge(u, v, weight=1, interaction=row['interaction'])
                
            for _, row in df_gd.iterrows():
                u, v = row['gene'], row['disease']
                self.G.add_node(u, type="gene")
                self.G.add_node(v, type="disease")
                self.G.add_edge(u, v, weight=1, association=row['association'])
        else:
            print("CSV datasets not found in data/")

    def suggest_drugs(self, disease_name):
        suggestions = []
        if disease_name not in self.G:
            return suggestions
            
        # Traverse disease -> gene -> drug
        genes = [n for n in self.G.neighbors(disease_name) if self.G.nodes[n].get('type') == 'gene']
        
        for gene in genes:
            drugs = [n for n in self.G.neighbors(gene) if self.G.nodes[n].get('type') == 'drug']
            for drug in drugs:
                # Find interaction details
                interaction = self.G[drug][gene].get('interaction', 'affects')
                association = self.G[gene][disease_name].get('association', 'linked to')
                
                explanation = f"Drug {drug} {interaction} Gene {gene} {association} Disease {disease_name}"
                
                # Check for existing
                existing = next((item for item in suggestions if item["drug"] == drug), None)
                if not existing:
                    suggestions.append({
                        "drug": drug,
                        "score": 0.85, # Base score
                        "confidence": "High",
                        "explanation": explanation,
                        "path": f"{drug} -> {gene} -> {disease_name}",
                        "involved_nodes": [drug, gene, disease_name],
                        "clinical_trial": True,
                        "breakdown": explanation
                    })
        
        return suggestions

    def get_graph_data(self):
        nodes = [{"id": n, "label": n, "type": self.G.nodes[n].get("type", "entity")} for n in self.G.nodes]
        edges = [{"from": u, "to": v, "weight": d.get("weight", 1)} for u, v, d in self.G.edges(data=True)]
        return {"nodes": nodes, "edges": edges}
