import transformers

# Add TF checkpoint folder 
saveNameBase = "/converting_tf_to_pt/bert-base-arabertv2-ViT-B-16-SigLIP-512-epoch-155-trained-2M"

ptFormer = transformers.AutoModel.from_pretrained(saveNameBase, from_tf=True)
ptFormer.save_pretrained(saveNameBase + "-PT")
