import pandas as pd
import os

# Create data directory if not exists
os.makedirs("data", exist_ok=True)

# 1. Symptom -> Disease Dataset
# Format: symptoms (comma separated), disease
symptom_disease_data = [
    # COVID-19
    ["fever,cough,shortness of breath,fatigue", "COVID-19"],
    ["fever,dry cough,loss of taste,loss of smell", "COVID-19"],
    ["sore throat,runny nose,headache,muscle pain", "COVID-19"],
    ["chills,nausea,vomiting,diarrhea", "COVID-19"],
    ["loss of appetite,congestion,sneezing", "COVID-19"],
    
    # Alzheimer's Disease
    ["memory loss,confusion,difficulty performing familiar tasks", "Alzheimer's Disease"],
    ["forgetfulness,disorientation,mood swings", "Alzheimer's Disease"],
    ["language problems,misplacing things,poor judgment", "Alzheimer's Disease"],
    ["withdrawal from social activities,personality changes", "Alzheimer's Disease"],
    ["difficulty planning or solving problems", "Alzheimer's Disease"],

    # Diabetes
    ["increased thirst,frequent urination,extreme hunger", "Diabetes"],
    ["unexplained weight loss,fatigue,blurred vision", "Diabetes"],
    ["slow-healing sores,frequent infections", "Diabetes"],
    ["tingling in hands or feet,dry skin", "Diabetes"],
    ["excessive thirst,weight loss,fatigue", "Diabetes"],

    # Heart Disease
    ["chest pain,shortness of breath,pain in arms/shoulders", "Heart Disease"],
    ["fatigue,fast heartbeat,shortness of breath", "Heart Disease"],
    ["dizziness,lightheadedness,fainting", "Heart Disease"],
    ["swelling in legs,ankles,or feet", "Heart Disease"],
    ["tightness in chest,upper body discomfort", "Heart Disease"],

    # Lung Cancer
    ["persistent cough,coughing up blood,chest pain", "Lung Cancer"],
    ["weight loss,bone pain,headache", "Lung Cancer"],
    ["hoarseness,shortness of breath,wheezing", "Lung Cancer"],
    ["feeling very tired or weak", "Lung Cancer"],
    ["recurrent infections like bronchitis", "Lung Cancer"],

    # Arthritis
    ["joint pain,stiffness,swelling", "Arthritis"],
    ["decreased range of motion,redness over joints", "Arthritis"],
    ["stiffness in the morning,warmth around joints", "Arthritis"],
    ["chronic pain,joint deformation", "Arthritis"],

    # Migraine
    ["headache,nausea,sensitivity to light", "Migraine"],
    ["throbbing pain,vomiting,blurred vision", "Migraine"],
    ["aura,sensitivity to sound,dizziness", "Migraine"],
    ["pain on one side of head,neck stiffness", "Migraine"]
]
# Expand data for better training
symptom_disease_df = pd.DataFrame(symptom_disease_data * 10, columns=["symptoms", "disease"])
symptom_disease_df.to_csv("data/symptom_disease.csv", index=False)

# 2. Drug -> Gene Dataset
# Format: drug,gene,interaction
drug_gene_data = [
    ["Remdesivir", "RNA Polymerase", "inhibits"],
    ["Chloroquine", "ACE2", "modulates"],
    ["Dexamethasone", "IL-6", "suppresses"],
    ["Baricitinib", "JAK1", "inhibits"],
    ["Baricitinib", "JAK2", "inhibits"],
    ["Donepezil", "AChE", "inhibits"],
    ["Memantine", "NMDA", "antagonizes"],
    ["Metformin", "AMPK", "activates"],
    ["Liraglutide", "GLP-1", "activates"],
    ["Ibuprofen", "COX-2", "inhibits"],
    ["Aspirin", "COX-1", "inhibits"],
    ["Tocilizumab", "IL-6R", "antagonizes"]
]
drug_gene_df = pd.DataFrame(drug_gene_data, columns=["drug", "gene", "interaction"])
drug_gene_df.to_csv("data/drug_gene.csv", index=False)

# 3. Gene -> Disease Dataset
# Format: gene,disease,association
gene_disease_data = [
    ["RNA Polymerase", "COVID-19", "pathway"],
    ["ACE2", "COVID-19", "receptor"],
    ["IL-6", "COVID-19", "cytokine"],
    ["JAK1", "COVID-19", "signaling"],
    ["JAK2", "COVID-19", "signaling"],
    ["AChE", "Alzheimer's Disease", "target"],
    ["NMDA", "Alzheimer's Disease", "receptor"],
    ["AMPK", "Diabetes", "metabolism"],
    ["GLP-1", "Diabetes", "hormone"],
    ["COX-2", "Heart Disease", "inflammation"],
    ["IL-6", "Lung Cancer", "inflammation"],
    ["JAK1", "Lung Cancer", "growth"],
    ["AChE", "Heart Disease", "regulation"]
]
gene_disease_df = pd.DataFrame(gene_disease_data, columns=["gene", "disease", "association"])
gene_disease_df.to_csv("data/gene_disease.csv", index=False)

print("Datasets created successfully in 'data/' folder.")
