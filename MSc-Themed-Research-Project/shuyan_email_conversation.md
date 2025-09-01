Re: Proposed methodology based on your paper



.tar
final_code.tar


Shuyan Li
​Barry Quinn (QMS);​Declan French;​Brandon Cochrane​
Hi Barry,
Thank you for your response.
I believe that 3,000–5,000 labeled images should be sufficient for training. My suggestion is to maintain the same data labeling format as in the paper so that we can directly replace the dataset (images, classnames.txt) and use the existing code without modifications. After we have some initial results, we can modify the model to improve the performance.
I have requested the code from the authors and attached it here. I think it would be beneficial to first run the code as is and then adapt it to our dataset. RS5M_ViT-H-14.pt is used for the pre-trained model, which can be downloaded from RS5M (3.8G). If any issues arise, I can also involve the author in the project if you’d like—he may be able to clarify any problems more effectively.
 
Best regards,
Shuyan
From: Barry Quinn (QMS) <b.quinn@qub.ac.uk>
Date: Wednesday, February 12, 2025 at 08:28
To: Shuyan Li <shuyan.li@qub.ac.uk>, Declan French <declan.french@qub.ac.uk>, Brandon Cochrane <bcochrane01@qub.ac.uk>
Subject: Proposed methodology based on your paper

Dear Shuyan,
 
Fantastic paper, which seems perfect for our problem statement. @Declan French and @Brandon Cochrane the methodology is this paper is ideal for our classification problem. I like the idea of an MSc student also. I am actually doing the AI masters as a part-time student although you may have some other MSc student in mind.
 
On reading the paper in more detail, I was thinking about an appropriate labelling strategy. We have about 60,000 images with flags from the top 50 towns in Northern Ireland, already pre-processed with bounding boxes. Your hierarchical prompting approach seems particularly relevant, especially how you structured the ship classification into primary/secondary/final categories.
 
I've drafted a proposed workflow adapting your methodology for our dataset engineering task:
 
Current Dataset:
- ~60,000 images with existing bounding boxes
- Sourced from 50 NI towns
- Mix of street-level and elevated viewpoints
- Various environmental conditions and contexts
 
Proposed Hierarchical Labeling Structure:
 
Level 1 (Primary Category):
- National
- Fraternal Order
- Sport
- Military
- Historical
- International Conflict
- Proscribed Organizations
 
Level 2 (Contextual/Physical Attributes):
- Display Context:
  * Building-mounted
  * Pole-mounted
  * Hand-carried (events)
  * Vehicle-mounted
- Physical Condition:
  * Fully visible
  * Partially obscured
  * Weather-affected
  * Damaged/worn
 
Level 3 (Specific Flag Identification):
[Example subset]
National:
- Union Jack
- Ulster Banner
- Irish Tricolor
- Scottish Saltire
- European Union
 
Fraternal:
- Orange Order (standard)
- Orange Order (specialized)
- Royal Black Institution
- Apprentice Boys
 
Sport:
- Northern Ireland Football
- Local Club Specifics
- GAA Related
 
Proposed Sampling Strategy:
- Initial target: 3,000-5,000 labeled images
- Stratified sampling by:
  * Town (ensuring representation from all 50 locations)
  * Primary categories
  * Seasonal distribution (capturing temporal variations)
 
Would this categorization structure align well with your prompt tuning methodology? We could adjust the hierarchy based on your experience with multi-level classification tasks.
 
Key Adaptations from Your Paper:
1. Using your hierarchical prompting structure but for flag categories (National, Fraternal, Sport, etc.)
2. Adapting the remote sensing priors concept to our context - in our case, environmental factors affecting flag visibility
3. Planning to use your attention visualization techniques to understand what features the model is using for classification
 
One key difference is our dataset already has bounding boxes, unlike your maritime imagery which needed full scene analysis. Would you recommend any modifications to the methodology given this advantage?
 
I've also started developing a web-based labeling tool to ensure consistent annotation quality. I can share the prototype if you're interested but I have attached an image of the frontend.

 
Would love your thoughts on this approach, particularly:
1. Is our target of 3,000-5,000 labeled images sufficient given your experience?
2. Should we modify the hierarchy structure for flags?
3. Any specific challenges you foresee in adapting your prompt tuning approach to this domain?
 
Thanks
 
Barry Quinn CStat | Senior Lecturer in Finance, Technology and Data Science, A Director of Finance and AI Research Lab | Website | GitHub | LinkedIn | CStat Profile |


From: Shuyan Li <shuyan.li@qub.ac.uk>
Sent: 06 February 2025 2:56 PM
To: Barry Quinn (QMS) <b.quinn@qub.ac.uk>
Subject: Re: Advice on our flag detection project
 
Hi Barry,
 
Please find the attached paper that might help.
By the way, I will supervise MSc AI project this year, which may start from May 2025. we may have the MSc student to do the experiments if needed. 
Best regards,
Shuyan
From: Barry Quinn (QMS) <b.quinn@qub.ac.uk>
Sent: 30 January 2025 09:09
To: Shuyan Li <shuyan.li@qub.ac.uk>
Subject: Re: Advice on our flag detection project
 
Hi Shuyan,
 
Yes, we have a PhD student on this project, who would have a background in econometrics, but their deep learning expertise would be limited.  So at the minute I am the only person in the project with any deep learning experience.  
 
We would be keen to fund another Ph.D. student with deep learning expertise as we want to repeat the identification and classification exercises for new historical google street view images we will be purchasing in the coming months.  There are many other CV challenges that would definitely make for a good PhD in Computer Vision.
 
For our current PhD student, we award this funding https://www.nidirect.gov.uk/articles/co-operative-awards-science-and-technology
and it could be an option again for a deep learning PhD expert.
 
I will also invite our current student to the meeting next week as he is very keen to learning.
 
Look forward to meeting you.
 
 
Barry Quinn CStat | Senior Lecturer in Finance, Technology and Data Science, A Director of Finance and AI Research Lab | Website | GitHub | LinkedIn | CStat Profile |


From: Shuyan Li <shuyan.li@qub.ac.uk>
Sent: 29 January 2025 5:16 PM
To: Barry Quinn (QMS) <b.quinn@qub.ac.uk>
Subject: Re: Advice on our flag detection project
 
Hi Barry,
 
Sure. See you next Thursday. 
 
I wonder if there is any PhD student with deep-learning experience for this project? And I wonder if the student will also attend the meeting?
 
Best regards,
Shuyan
From: Barry Quinn (QMS) <b.quinn@qub.ac.uk>
Sent: 29 January 2025 17:13
To: Shuyan Li <shuyan.li@qub.ac.uk>
Subject: Re: Advice on our flag detection project
 
What about 11am next Thursday?  I will send a team's invite.
 
 
Barry Quinn CStat | Senior Lecturer in Finance, Technology and Data Science, A Director of Finance and AI Research Lab | Website | GitHub | LinkedIn | CStat Profile |


From: Shuyan Li <shuyan.li@qub.ac.uk>
Sent: 29 January 2025 4:41 PM
To: Barry Quinn (QMS) <b.quinn@qub.ac.uk>
Subject: Re: Advice on our flag detection project
 
Hi Barry
 
Thank you very much for your information. I will be available tomorrow after 11am, next Thursday and Friday. 
Looking forward to hearing from you.
 
Best regards,
Shuyan
From: Barry Quinn (QMS) <b.quinn@qub.ac.uk>
Sent: 29 January 2025 12:47
To: Shuyan Li <shuyan.li@qub.ac.uk>
Subject: Advice on our flag detection project
 
Hi Shuyan,
 
Apologies for the long radio silence.  But it would you be free any time in the coming weeks to take more about our CV project and your potential collaboration?
 
It would probably be best if we set up a quick Teams call so I can explain more and start sharing what we have done so far. The data is roughly 2.2 million Google Street View images of the top 40 towns in Northern Ireland.
 
We using a multimodal off-the-shelf model called GroundingDINO.  We prompted the model to identify flags and hand validation the positives to remove false classification.
 
Anyway, let me know when you are free.
 
Thanks
 
 
Barry Quinn CStat | Senior Lecturer in Finance, Technology and Data Science, A Director of Finance and AI Research Lab | Website | GitHub | LinkedIn | CStat Profile |


From: Shuyan Li <shuyan.li@qub.ac.uk>
Sent: 16 October 2024 11:11 AM
To: Richard Gault <Richard.Gault@qub.ac.uk>; Barry Quinn (QMS) <b.quinn@qub.ac.uk>
Subject: Re: Advice on our flag detection project
 
Thank you, Richard.

 

Hi Barry,

 

It’s great to learn more about the project! I would be excited to see the existing dataset and understand its associated tasks. Thank you so much!

 

Best regards,

Shuyan

From: Richard Gault <Richard.Gault@qub.ac.uk>
Date: Wednesday, October 16, 2024 at 11:07
To: Barry Quinn (QMS) <b.quinn@qub.ac.uk>
Cc: Shuyan Li <shuyan.li@qub.ac.uk>
Subject: Re: Advice on our flag detection project

Hi Barry,

 

Hope things are going well. Please may I introduce Dr Shuyan Li (CC'd). Shuyan has recently started as a lecturer in the school specialising in Computer Vision having great success across a wide range of topics in the field. Shuyan would be interested to learn more about the project and opportunities to collaborate. 

 

I shall hand things over to you for further discussions and hope there are good synergies to collaborate.

 

kind regards,

 

Richard

From: Barry Quinn (QMS) <b.quinn@qub.ac.uk>
Sent: Wednesday, October 9, 2024 09:43
To: Richard Gault <Richard.Gault@qub.ac.uk>; Computer Vision @ Queen's <computervision@qub.ac.uk>
Subject: Advice on our flag detection project

 

Hi Richard and Team,

 

I hope all is well with you.  We want some advice and guidance on improving flag detection algorithms. We have a new PhD student starting this week who will repeat our initial analysis of historical images to create a longitudinal sample, providing a rich sample to perform downstream explanatory regressions.

 

I want some advice or guidance on improving our approach and reducing the false positive rate using a sample of hand-crafted false positives (and true positives) from our first run.  Our current approach uses the off-the-shelf GroundingDINO multimodal model, but we spent considerable time hand-filtering the false positives.  I guess my thought is how to cost-effective fine-tune/improve this model or just train a new model from scratch (or a combination of both, maybe)

 

I would greatly appreciate any help or guidance you can give me.  We are also open to a more formal third supervisor role for this PHD project if anyone would be interested.

 

Thanks

 

 

Barry Quinn CStat | Senior Lecturer in Finance, Technology and Data Science, A Director of Finance and AI Research Lab | Website | GitHub | LinkedIn | CStat Profile |



