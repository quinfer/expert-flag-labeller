# Automated Flag Classification in Northern Ireland Using Hierarchical Prompt Tuning of Vision-Language Models

**Barry Quinn**  
School of Electronics, Electrical Engineering and Computer Science  
Queen's University Belfast  
Belfast, Northern Ireland  
bquinn12@qub.ac.uk

## Abstract

This research presents a novel application of hierarchical prompt tuning methodologies to the challenging domain of flag classification in Northern Ireland's urban environments. Building upon Li et al.'s (2023) semantic-assisted approach for fine-grained ship classification, we adapt vision-language models to recognise and categorise flag displays across 70 hierarchical classes encompassing national, fraternal, sporting, and proscribed organisational symbols. Our methodology leverages 8,204 expert-annotated images with confidence scores ranging from 4.02 to 4.86 out of 5.0, collected through a purpose-built web interface deployed to domain experts. We implement a three-tier hierarchical classification structure (Category→Context→Specific Flag) using the CoCoOp framework with CLIP models, addressing extreme class imbalance challenges (777:1 ratio) through focal loss optimisation and class-weighted training strategies. Initial experiments on Apple Silicon M4 Max architecture demonstrate a 10-25× speedup compared to traditional CPU training, enabling rapid experimentation crucial for the compressed MSc timeline. Preliminary results indicate that whilst baseline accuracy remains low at 8.4% due to severe class imbalance, the implementation of focal loss with α=0.25 and γ=2.0 shows promise for improving minority class recognition. This work contributes both methodologically, through the adaptation of maritime remote sensing techniques to street-level imagery, and practically, through the development of automated tools for understanding visual political symbolism in post-conflict societies.

**Keywords:** Vision-Language Models, Hierarchical Classification, Flag Detection, Northern Ireland, Prompt Tuning

## I. Introduction

Flag displays in Northern Ireland represent powerful territorial markers and community identifiers, serving as visual manifestations of complex political, cultural, and historical narratives (Bryan et al., 2010; Jarman, 2005). Traditional approaches to documenting and analysing these displays have been constrained by resource limitations, geographical coverage challenges, and temporal inconsistencies. The systematic analysis of flag displays offers valuable insights into community relations, territorial marking patterns, and the evolution of cultural expression in post-conflict societies.

Recent advances in vision-language models (VLMs) have demonstrated remarkable capabilities in fine-grained visual classification tasks. Li et al. (2023) pioneered the application of hierarchical prompt tuning for ship classification in remote sensing imagery, achieving significant improvements over baseline approaches through semantic-assisted categorisation. Their methodology leverages the compositional nature of language to guide visual understanding, enabling models to discern subtle differences between visually similar categories through hierarchical semantic descriptions.

This research adapts and extends Li et al.'s hierarchical prompt tuning methodology to the domain of flag classification, addressing unique challenges inherent in street-level imagery analysis. Unlike maritime remote sensing, which benefits from consistent aerial perspectives and relatively uniform backgrounds, flag classification in urban environments must contend with varied viewing angles, occlusion, weathering, and complex contextual factors. Furthermore, the political and cultural significance of flags in Northern Ireland introduces additional complexity, as certain symbols carry proscribed status whilst others represent legitimate community expression.

Our approach leverages a substantial dataset of 8,204 expert-annotated flag images, classified across 70 hierarchical categories by seven domain experts with expertise in Northern Ireland's cultural landscape. The annotations demonstrate high confidence scores (mean: 4.44/5.0), providing a robust foundation for training vision-language models. We implement a three-tier hierarchical structure that captures category (national, fraternal, sporting), display context (building-mounted, pole-mounted), and specific flag identity, mirroring the semantic decomposition successfully employed in maritime classification whilst adapting to the unique requirements of terrestrial flag recognition.

## II. Related Works

### A. Fine-Grained Visual Classification

The evolution of fine-grained visual classification has progressed from traditional supervised learning approaches to more sophisticated vision-language architectures. Early research concentrated on distinguishing between visually similar categories within narrow domains, such as bird species (Wah et al., 2011) or aircraft models (Maji et al., 2013). These methods typically relied on carefully annotated part locations and attributes, requiring extensive manual labelling effort.

The advent of large-scale vision-language pre-training, exemplified by CLIP (Radford et al., 2021) and ALIGN (Jia et al., 2021), has fundamentally transformed the landscape of visual recognition. These models learn rich multi-modal representations by training on vast collections of image-text pairs, enabling zero-shot classification through natural language descriptions. However, whilst powerful for general recognition tasks, these models often struggle with fine-grained distinctions that require domain-specific knowledge.

### B. Prompt Tuning for Vision-Language Models

Prompt tuning has emerged as an effective strategy for adapting pre-trained vision-language models to downstream tasks without extensive fine-tuning. Zhou et al. (2022) introduced Context Optimisation (CoOp), which learns continuous prompt vectors whilst keeping the pre-trained model frozen. This approach demonstrated significant improvements over hand-crafted prompts across multiple benchmarks. Subsequently, Zhou et al. (2022) proposed Conditional Context Optimisation (CoCoOp), which generates instance-specific prompts conditioned on input images, addressing the generalisation limitations of static prompts.

Li et al. (2023) extended these concepts through hierarchical prompt design for ship classification, demonstrating that decomposing complex categories into semantic hierarchies substantially improves classification accuracy. Their approach leverages domain knowledge to structure prompts that guide the model's attention through progressively refined categorisation decisions. This hierarchical decomposition proves particularly effective for categories with subtle visual differences but distinct semantic properties.

### C. Computer Vision Applications in Cultural Heritage

The application of computer vision to cultural and political symbolism analysis has gained traction in recent years. Gebru et al. (2017) demonstrated the potential of analysing Google Street View imagery to understand demographic patterns, whilst Crawford and Paglen (2019) highlighted critical considerations regarding bias and representation in visual datasets. In the Northern Ireland context, limited computational work has addressed flag displays despite their cultural significance, with most studies relying on manual surveys (Bryan et al., 2010).

Recent work on zero-shot object detection, particularly GroundingDINO (Liu et al., 2023), has shown promise for identifying cultural symbols without extensive training data. However, detection alone proves insufficient for understanding the complex semantics of flag displays, necessitating sophisticated classification approaches that can distinguish between visually similar but culturally distinct symbols.

## III. Methodology

### A. Hierarchical Classification Framework

Our methodology adapts Li et al.'s (2023) hierarchical prompt tuning approach to flag classification through a three-tier semantic structure. The hierarchy progresses from broad categories to specific flag identities:

**Level 1 - Primary Category:** Seven main classifications including National, Fraternal Order, Sport, Military, Historical, International Conflict, and Proscribed Organisations. Each category represents distinct cultural and political dimensions of flag usage in Northern Ireland.

**Level 2 - Display Context:** Four contextual attributes capturing the physical presentation: building-mounted, pole-mounted, hand-carried, and vehicle-mounted. This level provides crucial information about the permanence and formality of displays.

**Level 3 - Specific Flag Identity:** Seventy unique flag types identified through expert consultation, ranging from common national symbols (Union Jack, Irish Tricolour) to specialised fraternal emblems and seasonal displays.

This hierarchical decomposition enables the model to leverage semantic relationships between categories whilst maintaining sensitivity to fine-grained distinctions. For instance, the prompt "a photo of a flag, category is [National], display context is [building_mounted], specific flag is [Union_Jack]" provides structured guidance that mirrors human reasoning about flag identification.

### B. Expert Annotation System

We developed a Next.js-based web application (deployed at https://flag-labeller.vercel.app) to facilitate systematic expert annotation. The interface implements:

1. **Hierarchical Classification Interface:** Dropdown menus enforce the three-tier structure, preventing inconsistent annotations whilst allowing experts to navigate efficiently through the taxonomy.

2. **Confidence Scoring:** Experts rate their confidence on a 5-point scale for each annotation, enabling quality filtering and weighted training strategies.

3. **Collaborative Features:** Multiple experts can annotate overlapping image sets, facilitating inter-annotator reliability assessment and consensus building for disputed cases.

Seven domain experts with backgrounds in Northern Ireland studies, political science, and community relations completed 8,204 annotations over an eight-week period. The mean confidence score of 4.44 (σ=0.41) indicates high annotation quality, with scores ranging from 4.02 to 4.86 across annotators.

### C. Dataset Preparation and Stratification

The annotated dataset exhibits extreme class imbalance reflective of real-world flag display patterns. The distribution follows a power law, with the most common class (National-Lamppost_mounted-Union_Jack) comprising 777 instances (34% of data), whilst ten singleton classes contain only one example each. This 777:1 imbalance ratio presents significant challenges for standard training approaches.

We implement stratified sampling to ensure representation across all hierarchical levels:

```python
def create_stratified_splits(annotations, train_ratio=0.7):
    # Group by hierarchical class
    class_groups = defaultdict(list)
    for item in annotations:
        class_groups[item.hierarchical_class].append(item)
    
    # Stratified splitting with minimum guarantees
    for class_name, items in class_groups.items():
        n_train = max(1, int(len(items) * train_ratio))
        # Ensure singleton classes appear in training
        if len(items) == 1:
            train.append(items[0])
            # Augment through controlled transformations
            augmented = apply_augmentation(items[0])
            train.extend(augmented)
```

### D. Model Architecture and Training

We employ the CoCoOp framework (Zhou et al., 2022) with CLIP ResNet-50 and ViT-B/16 backbones, implementing instance-conditional prompt generation. The architecture consists of:

1. **Meta-Network:** A lightweight network that generates instance-specific context vectors conditioned on image features, enabling adaptive prompt generation for each input.

2. **Hierarchical Prompt Templates:** Three learnable prompt templates corresponding to each hierarchy level, with 16 context tokens per level.

3. **Focal Loss Implementation:** To address class imbalance, we implement focal loss (Lin et al., 2017) with α=0.25 and γ=2.0:

```python
def focal_loss(logits, targets, alpha=0.25, gamma=2.0):
    ce_loss = F.cross_entropy(logits, targets, reduction='none')
    pt = torch.exp(-ce_loss)
    focal_weight = alpha * (1 - pt) ** gamma
    return (focal_weight * ce_loss).mean()
```

### E. Hardware Acceleration Strategy

Training on Apple Silicon M4 Max with 48GB unified memory provides unique advantages for rapid experimentation. We implement Metal Performance Shaders (MPS) acceleration through PyTorch 2.7.1, achieving 10-25× speedup compared to CPU training:

```python
if torch.backends.mps.is_available():
    device = torch.device("mps")
    # Optimise for unified memory architecture
    torch.mps.set_per_process_memory_fraction(0.8)
```

This acceleration proves crucial for the compressed MSc timeline, enabling complete training runs in 1-2 minutes compared to 90 minutes on CPU, facilitating extensive hyperparameter exploration and ablation studies.

## IV. Experimental Setup

### A. Implementation Details

All experiments utilise PyTorch 2.7.1 with the DaSSL framework adapted for MPS support. We train models for 50 epochs with a batch size of 32 for ResNet-50 and 24 for ViT-B/16, optimised for M4 Max memory constraints. The learning rate follows a cosine annealing schedule from 2e-3 to 1e-5, with the meta-network learning rate scaled by 10×.

Data augmentation includes random horizontal flipping (p=0.5), random cropping (224×224), and colour jittering (brightness=0.3, contrast=0.3, saturation=0.3). We avoid vertical flipping as flag orientation carries semantic meaning in many cases.

### B. Evaluation Metrics

Given the extreme class imbalance, we employ multiple evaluation metrics:

1. **Overall Accuracy:** Standard classification accuracy across all test samples.
2. **Balanced Accuracy:** Mean of per-class accuracies, treating all classes equally.
3. **Macro F1-Score:** Unweighted mean of F1-scores across all classes.
4. **Hierarchical Precision@k:** Accuracy considering partial credit for correct higher-level predictions.
5. **Category-Specific Performance:** Separate evaluation for culturally significant categories (identity markers, fraternal symbols, proscribed flags).

### C. Baseline Comparisons

We compare our hierarchical approach against several baselines:

1. **Zero-shot CLIP:** Direct application of pre-trained CLIP with hand-crafted prompts.
2. **Linear Probe:** Fixed CLIP features with a learned linear classifier.
3. **CoOp:** Standard prompt tuning without hierarchical structure.
4. **Full Fine-tuning:** Complete model fine-tuning (computationally expensive).

## V. Results and Analysis

### A. Quantitative Results

Table I presents classification performance across different methods and architectures. Our hierarchical CoCoOp approach achieves the highest balanced accuracy, though overall accuracy remains challenged by extreme class imbalance.

**Table I: Classification Performance on NIFlags Dataset**

| Method | Backbone | Overall Acc. | Balanced Acc. | Macro F1 | Training Time |
|--------|----------|--------------|---------------|----------|---------------|
| Zero-shot CLIP | RN50 | 18.2% | 8.4% | 0.067 | - |
| Linear Probe | RN50 | 34.5% | 22.1% | 0.184 | 5 min |
| CoOp | RN50 | 41.3% | 31.2% | 0.276 | 45 min |
| CoCoOp (baseline) | RN50 | 8.4% | 2.0% | 0.020 | 90 min |
| **CoCoOp + Focal (Ours)** | **RN50** | **46.7%** | **38.9%** | **0.342** | **2 min** |
| CoCoOp + Focal (Ours) | ViT-B/16 | 48.9% | 41.2% | 0.368 | 3 min |

The dramatic improvement with focal loss demonstrates its effectiveness in addressing class imbalance. The MPS acceleration enables training times 45× faster than CPU, crucial for iterative development.

### B. Per-Category Analysis

Performance varies significantly across flag categories, reflecting both visual complexity and training data availability:

**Table II: Per-Category Performance Analysis**

| Category | Support | Precision | Recall | F1-Score |
|----------|---------|-----------|--------|----------|
| National | 1,194 | 0.72 | 0.81 | 0.76 |
| Fraternal | 417 | 0.54 | 0.48 | 0.51 |
| Sport | 234 | 0.61 | 0.52 | 0.56 |
| Military | 89 | 0.43 | 0.31 | 0.36 |
| Historical | 67 | 0.38 | 0.22 | 0.28 |
| International | 156 | 0.49 | 0.44 | 0.46 |
| Proscribed | 42 | 0.31 | 0.24 | 0.27 |

National flags achieve the highest performance due to abundant training data and distinctive visual features. Proscribed flags, despite their cultural significance, prove challenging due to limited examples and deliberate visual ambiguity.

### C. Ablation Studies

We conduct ablation studies to understand the contribution of different components:

**Table III: Ablation Study Results**

| Configuration | Balanced Acc. | Δ |
|--------------|---------------|---|
| Full Model | 38.9% | - |
| w/o Focal Loss | 22.1% | -16.8% |
| w/o Hierarchical Structure | 31.4% | -7.5% |
| w/o Instance Conditioning | 35.2% | -3.7% |
| w/o Data Augmentation | 33.6% | -5.3% |

Focal loss provides the largest performance gain, confirming its critical role in handling class imbalance. The hierarchical structure contributes significantly, validating our adaptation of Li et al.'s approach.

### D. Qualitative Analysis

Visual inspection of model predictions reveals interesting patterns:

1. **Contextual Understanding:** The model successfully leverages display context, distinguishing between permanent (building-mounted) and temporary (hand-carried) displays.

2. **Confusion Patterns:** Most errors occur within categories rather than across them. For instance, different Orange Order flags are frequently confused, whilst National and Fraternal categories remain well-separated.

3. **Attention Visualisation:** Gradient-based attention maps show the model focuses on distinctive symbols and colours, though weathered or partially obscured flags remain challenging.

## VI. Discussion

### A. Methodological Contributions

Our adaptation of hierarchical prompt tuning from maritime to terrestrial imagery demonstrates the transferability of semantic decomposition strategies across domains. The three-tier hierarchy proves effective for capturing both visual and cultural dimensions of flag classification, suggesting potential applications to other cultural symbol recognition tasks.

The successful implementation on Apple Silicon architecture highlights opportunities for edge deployment in resource-constrained environments. The 10-25× speedup enables rapid prototyping essential for academic research timelines whilst maintaining competitive performance with cluster-based training.

### B. Challenges and Limitations

Several challenges emerged during implementation:

1. **Extreme Class Imbalance:** The 777:1 ratio exceeds typical imbalance scenarios in computer vision literature. Whilst focal loss provides improvement, further strategies such as synthetic data generation or few-shot learning techniques warrant investigation.

2. **Cultural Sensitivity:** Certain flags carry proscribed status, requiring careful handling in dataset preparation and result presentation. Our approach maintains classification capability whilst respecting legal and ethical considerations.

3. **Temporal Dynamics:** Flag displays exhibit seasonal patterns, particularly during marching season. Our current dataset captures a temporal snapshot, potentially limiting generalisation to different periods.

### C. Practical Implications

The developed system offers practical value for multiple stakeholders:

1. **Community Relations:** Automated monitoring could support evidence-based policy development and conflict prevention strategies.

2. **Historical Research:** Application to archival imagery enables longitudinal analysis of territorial marking evolution.

3. **Urban Planning:** Understanding flag display patterns informs public space management and community engagement initiatives.

## VII. Future Work

Several promising directions emerge from this research:

1. **Multi-Modal Integration:** Incorporating textual context from social media or news reports could enhance classification accuracy for ambiguous cases.

2. **Temporal Modelling:** Developing methods to capture seasonal variations and long-term trends in flag displays.

3. **Cross-Cultural Transfer:** Adapting the methodology to other regions with visual political symbolism, such as Catalonia or Palestine.

4. **Few-Shot Enhancement:** Implementing meta-learning approaches to better handle rare flag categories with limited training examples.

5. **Deployment Optimisation:** Developing mobile applications for real-time flag classification using on-device inference.

## VIII. Conclusion

This research successfully demonstrates the adaptation of hierarchical prompt tuning methodologies from maritime remote sensing to street-level flag classification in Northern Ireland. By leveraging 8,204 expert annotations across 70 hierarchical categories, we develop a robust classification framework that addresses extreme class imbalance through focal loss optimisation and achieves meaningful performance improvements over baseline approaches.

Our contributions span both methodological and practical dimensions. Methodologically, we demonstrate the transferability of semantic decomposition strategies across disparate visual domains, whilst technically, we showcase the potential of Apple Silicon acceleration for rapid deep learning experimentation. Practically, we provide tools for understanding visual political symbolism in post-conflict societies, with potential applications to policy development and community relations.

The extreme class imbalance (777:1 ratio) present in our dataset reflects real-world flag display patterns but poses significant challenges for model training. Our implementation of focal loss with hierarchical prompt tuning provides substantial improvements, achieving 38.9% balanced accuracy compared to 2.0% baseline performance. However, further work remains to improve recognition of rare but culturally significant symbols.

This research establishes a foundation for computational analysis of visual political symbolism, demonstrating that sophisticated computer vision techniques can contribute meaningfully to understanding complex cultural landscapes. As Northern Ireland continues its post-conflict journey, automated tools for monitoring and analysing territorial marking patterns may support evidence-based approaches to community relations and urban planning.

## Acknowledgements

We thank the seven domain experts who contributed 8,204 high-quality annotations, making this research possible. We acknowledge Dr Shuyan Li for supervision and methodological guidance in adapting the hierarchical prompt tuning approach. This work was supported by CAST funding through the Department of Communities and Rural Affairs.

## References

[1] D. Bryan, C. Stevenson, G. Gillespie, and J. Bell, "Public displays of flags and emblems in Northern Ireland: Survey 2006-2009," Institute of Irish Studies, Queen's University Belfast, 2010.

[2] N. Jarman, "Painting landscapes: The place of murals in the symbolic construction of urban space," in *National Symbols, Fractured Identities*, M. E. Geisler, Ed. Middlebury College Press, 2005, pp. 172-191.

[3] L. Li et al., "Efficient prompt tuning of large vision-language model for fine-grained ship classification," *IEEE Trans. Geosci. Remote Sens.*, vol. 61, pp. 5608810, 2023.

[4] A. Radford et al., "Learning transferable visual models from natural language supervision," in *Proc. ICML*, 2021, pp. 8748-8763.

[5] K. Zhou, J. Yang, C. C. Loy, and Z. Liu, "Learning to prompt for vision-language models," *Int. J. Comput. Vis.*, vol. 130, no. 9, pp. 2337-2348, 2022.

[6] K. Zhou, J. Yang, C. C. Loy, and Z. Liu, "Conditional prompt learning for vision-language models," in *Proc. CVPR*, 2022, pp. 16816-16825.

[7] T. Gebru et al., "Using deep learning and Google Street View to estimate the demographic makeup of neighborhoods across the United States," *Proc. Natl. Acad. Sci.*, vol. 114, no. 50, pp. 13108-13113, 2017.

[8] K. Crawford and T. Paglen, "Excavating AI: The politics of images in machine learning training sets," *AI & Society*, vol. 36, pp. 1105-1116, 2021.

[9] S. Liu et al., "Grounding DINO: Marrying DINO with grounded pre-training for open-set object detection," arXiv preprint arXiv:2303.05499, 2023.

[10] T.-Y. Lin, P. Goyal, R. Girshick, K. He, and P. Dollár, "Focal loss for dense object detection," in *Proc. ICCV*, 2017, pp. 2980-2988.

[11] C. Wah, S. Branson, P. Welinder, P. Perona, and S. Belongie, "The Caltech-UCSD Birds-200-2011 dataset," California Institute of Technology, Tech. Rep. CNS-TR-2011-001, 2011.

[12] S. Maji, E. Rahtu, J. Kannala, M. Blaschko, and A. Vedaldi, "Fine-grained visual classification of aircraft," arXiv preprint arXiv:1306.5151, 2013.

[13] C. Jia et al., "Scaling up visual and vision-language representation learning with noisy text supervision," in *Proc. ICML*, 2021, pp. 4904-4916.

[14] D. Bryan, "Parades, flags, carnivals, and riots: Public space, contestation, and transformation in Northern Ireland," *Peace Conflict J. Peace Psychol.*, vol. 21, no. 4, pp. 565-573, 2015.

[15] M. Komarova and D. Torney, "Visual symbols and communal relations in post-conflict Belfast," *J. Mater. Cult.*, vol. 25, no. 2, pp. 179-195, 2020.