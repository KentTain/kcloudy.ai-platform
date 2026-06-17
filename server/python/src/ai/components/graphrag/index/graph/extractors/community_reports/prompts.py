"""包含提示词定义的文件."""

COMMUNITY_REPORT_PROMPT = """。
You are an AI assistant that helps a human analyst to perform general information discovery. Information discovery is the process of identifying and assessing relevant information associated with certain entities (e.g., organizations and individuals) within a network.

# Goal
Write a comprehensive report of a community, given a list of entities that belong to the community as well as their relationships and optional associated claims. The report will be used to inform decision-makers about information associated with the community and their potential impact. The content of this report includes an overview of the community's key entities, their legal compliance, technical capabilities, reputation, and noteworthy claims.

# Report Structure

The report should include the following sections:

- TITLE: community's name that represents its key entities - title should be short but specific. When possible, include representative named entities in the title.
- SUMMARY: An executive summary of the community's overall structure, how its entities are related to each other, and significant information associated with its entities.
- IMPACT SEVERITY RATING: a float score between 0-10 that represents the severity of IMPACT posed by entities within the community.  IMPACT is the scored importance of a community.
- RATING EXPLANATION: Give a single sentence explanation of the IMPACT severity rating.
- DETAILED FINDINGS: A list of 5-10 key insights about the community. Each insight should have a short summary followed by multiple paragraphs of explanatory text grounded according to the grounding rules below. Be comprehensive.

Return output as a well-formed JSON-formatted string with the following format:
    {{
        "title": <report_title>,
        "summary": <executive_summary>,
        "rating": <impact_severity_rating>,
        "rating_explanation": <rating_explanation>,
        "findings": [
            {{
                "summary":<insight_1_summary>,
                "explanation": <insight_1_explanation>
            }},
            {{
                "summary":<insight_2_summary>,
                "explanation": <insight_2_explanation>
            }}
        ]
    }}

# Grounding Rules

Points supported by data should list their data references as follows:

"This is an example sentence supported by multiple data references [Data: <dataset name> (record ids); <dataset name> (record ids)]."

Do not list more than 5 record ids in a single reference. Instead, list the top 5 most relevant record ids and add "+more" to indicate that there are more.

For example:
"Person X is the owner of Company Y and subject to many allegations of wrongdoing [Data: Reports (1), Entities (5, 7); Relationships (23); Claims (7, 2, 34, 64, 46, +more)]."

where 1, 5, 7, 23, 2, 34, 46, and 64 represent the id (not the index) of the relevant data record.

Do not include information where the supporting evidence for it is not provided.


# Example Input
-----------
Text:

Entities

id,entity,description
5,VERDANT OASIS PLAZA,Verdant Oasis Plaza is the location of the Unity March
6,HARMONY ASSEMBLY,Harmony Assembly is an organization that is holding a march at Verdant Oasis Plaza

Relationships

id,source,target,description
37,VERDANT OASIS PLAZA,UNITY MARCH,Verdant Oasis Plaza is the location of the Unity March
38,VERDANT OASIS PLAZA,HARMONY ASSEMBLY,Harmony Assembly is holding a march at Verdant Oasis Plaza
39,VERDANT OASIS PLAZA,UNITY MARCH,The Unity March is taking place at Verdant Oasis Plaza
40,VERDANT OASIS PLAZA,TRIBUNE SPOTLIGHT,Tribune Spotlight is reporting on the Unity march taking place at Verdant Oasis Plaza
41,VERDANT OASIS PLAZA,BAILEY ASADI,Bailey Asadi is speaking at Verdant Oasis Plaza about the march
43,HARMONY ASSEMBLY,UNITY MARCH,Harmony Assembly is organizing the Unity March

Output:
{{
    "title": "Verdant Oasis Plaza and Unity March",
    "summary": "The community revolves around the Verdant Oasis Plaza, which is the location of the Unity March. The plaza has relationships with the Harmony Assembly, Unity March, and Tribune Spotlight, all of which are associated with the march event.",
    "rating": 5.0,
    "rating_explanation": "The impact severity rating is moderate due to the potential for unrest or conflict during the Unity March.",
    "findings": [
        {{
            "summary": "Verdant Oasis Plaza as the central location",
            "explanation": "Verdant Oasis Plaza is the central entity in this community, serving as the location for the Unity March. This plaza is the common link between all other entities, suggesting its significance in the community. The plaza's association with the march could potentially lead to issues such as public disorder or conflict, depending on the nature of the march and the reactions it provokes. [Data: Entities (5), Relationships (37, 38, 39, 40, 41,+more)]"
        }},
        {{
            "summary": "Harmony Assembly's role in the community",
            "explanation": "Harmony Assembly is another key entity in this community, being the organizer of the march at Verdant Oasis Plaza. The nature of Harmony Assembly and its march could be a potential source of threat, depending on their objectives and the reactions they provoke. The relationship between Harmony Assembly and the plaza is crucial in understanding the dynamics of this community. [Data: Entities(6), Relationships (38, 43)]"
        }},
        {{
            "summary": "Unity March as a significant event",
            "explanation": "The Unity March is a significant event taking place at Verdant Oasis Plaza. This event is a key factor in the community's dynamics and could be a potential source of threat, depending on the nature of the march and the reactions it provokes. The relationship between the march and the plaza is crucial in understanding the dynamics of this community. [Data: Relationships (39)]"
        }},
        {{
            "summary": "Role of Tribune Spotlight",
            "explanation": "Tribune Spotlight is reporting on the Unity March taking place in Verdant Oasis Plaza. This suggests that the event has attracted media attention, which could amplify its impact on the community. The role of Tribune Spotlight could be significant in shaping public perception of the event and the entities involved. [Data: Relationships (40)]"
        }}
    ]
}}


# Real Data

Use the following text for your answer. Do not make anything up in your answer.

Text:
{input_text}

The report should include the following sections:

- TITLE: community's name that represents its key entities - title should be short but specific. When possible, include representative named entities in the title.
- SUMMARY: An executive summary of the community's overall structure, how its entities are related to each other, and significant information associated with its entities.
- IMPACT SEVERITY RATING: a float score between 0-10 that represents the severity of IMPACT posed by entities within the community.  IMPACT is the scored importance of a community.
- RATING EXPLANATION: Give a single sentence explanation of the IMPACT severity rating.
- DETAILED FINDINGS: A list of 5-10 key insights about the community. Each insight should have a short summary followed by multiple paragraphs of explanatory text grounded according to the grounding rules below. Be comprehensive.

Return output as a well-formed JSON-formatted string with the following format:
    {{
        "title": <report_title>,
        "summary": <executive_summary>,
        "rating": <impact_severity_rating>,
        "rating_explanation": <rating_explanation>,
        "findings": [
            {{
                "summary":<insight_1_summary>,
                "explanation": <insight_1_explanation>
            }},
            {{
                "summary":<insight_2_summary>,
                "explanation": <insight_2_explanation>
            }}
        ]
    }}

# Grounding Rules

Points supported by data should list their data references as follows:

"This is an example sentence supported by multiple data references [Data: <dataset name> (record ids); <dataset name> (record ids)]."

Do not list more than 5 record ids in a single reference. Instead, list the top 5 most relevant record ids and add "+more" to indicate that there are more.

For example:
"Person X is the owner of Company Y and subject to many allegations of wrongdoing [Data: Reports (1), Entities (5, 7); Relationships (23); Claims (7, 2, 34, 64, 46, +more)]."

where 1, 5, 7, 23, 2, 34, 46, and 64 represent the id (not the index) of the relevant data record.

Do not include information where the supporting evidence for it is not provided.

Output:"""


COMMUNITY_REPORT_PROMPT_ZH = """。
你是一个AI助手,帮助人类分析师进行一般信息发现。信息发现是识别和评估网络中与某些实体(如组织和个人)相关的相关信息的过程。

# 目标
给定一个社区的实体列表及其关系和可选的关联声明,撰写一份全面的社区报告。该报告将用于告知决策者与该社区相关的信息及其潜在影响。报告内容包括社区关键实体的概述、其法律合规性、技术能力、声誉和值得注意的声明。

# 报告结构

报告应包括以下部分:

- TITLE: 代表社区关键实体的社区名称 - 标题应简短但具体。尽可能在标题中包含代表性的命名实体。
- SUMMARY: 社区整体结构的执行摘要,其实体如何相互关联,以及与其实体相关的重要信息。
- IMPACT SEVERITY RATING: 一个0-10之间的浮点分数,表示社区内实体所构成影响的严重程度。IMPACT是社区的重要性评分。
- RATING EXPLANATION: 用一句话解释影响严重程度评级。
- DETAILED FINDINGS: 关于社区的5-10个关键见解列表。每个见解应有一个简短摘要,后跟多段解释性文本,根据下面的引用规则进行引用。要全面。

以格式良好的YAML格式字符串返回输出,格式如下:
    title: <报告标题>
    summary: <执行摘要>
    rating: <影响严重程度评级>
    rating_explanation: <评级解释>
    findings:
      - summary: <见解1摘要>
        explanation: <见解1解释>
      - summary: <见解2摘要>
        explanation: <见解2解释>

# 引用规则

由数据支持的要点应列出其数据引用,如下所示:

"这是一个由多个数据引用支持的示例句子[数据: <数据集名称> (记录ID); <数据集名称> (记录ID)]。"

单个引用中不要列出超过5个记录ID。而是列出最相关的5个记录ID,并添加"+更多"表示还有更多。

例如:
"人物X是公司Y的所有者,并受到许多不当行为的指控[数据: 报告 (1), 实体 (5, 7); 关系 (23); 声明 (7, 2, 34, 64, 46, +更多)]。"

其中1、5、7、23、2、34、46和64表示相关数据记录的ID(不是索引)。

不要包含没有提供支持证据的信息。


# 示例输入
-----------
文本:

实体

id,entity,description
5,绿洲广场,绿洲广场是团结游行的地点
6,和谐集会,和谐集会是一个在绿洲广场举行游行的组织

关系

id,source,target,description
37,绿洲广场,团结游行,绿洲广场是团结游行的地点
38,绿洲广场,和谐集会,和谐集会正在绿洲广场举行游行
39,绿洲广场,团结游行,团结游行正在绿洲广场举行
40,绿洲广场,论坛焦点,论坛焦点正在报道在绿洲广场举行的团结游行
41,绿洲广场,贝利·阿萨迪,贝利·阿萨迪正在绿洲广场就游行发表演讲
43,和谐集会,团结游行,和谐集会正在组织团结游行

输出:
title: "绿洲广场与团结游行"
summary: "该社区围绕绿洲广场展开,绿洲广场是团结游行的地点。广场与和谐集会、团结游行和论坛焦点都有关系,这些都与游行活动相关。"
rating: 5.0
rating_explanation: "影响严重程度评级为中等,因为团结游行期间可能存在骚乱或冲突的潜在风险。"
findings:
  - summary: "绿洲广场作为中心地点"
    explanation: "绿洲广场是该社区的中心实体,是团结游行的地点。这个广场是所有其他实体之间的共同联系,表明其在社区中的重要性。广场与游行的关联可能会导致公共秩序问题或冲突,具体取决于游行的性质及其引发的反应。[数据: 实体 (5), 关系 (37, 38, 39, 40, 41,+更多)]"
  - summary: "和谐集会在社区中的角色"
    explanation: "和谐集会是该社区的另一个关键实体,是在绿洲广场组织游行的组织。和谐集会及其游行的性质可能是潜在威胁的来源,具体取决于他们的目标及其引发的反应。和谐集会与广场之间的关系对于理解该社区的动态至关重要。[数据: 实体(6), 关系 (38, 43)]"
  - summary: "团结游行作为重要事件"
    explanation: "团结游行是在绿洲广场举行的重要事件。该事件是社区动态的关键因素,可能是潜在威胁的来源,具体取决于游行的性质及其引发的反应。游行与广场之间的关系对于理解该社区的动态至关重要。[数据: 关系 (39)]"
  - summary: "论坛焦点的角色"
    explanation: "论坛焦点正在报道在绿洲广场举行的团结游行。这表明该事件已引起媒体关注,这可能会放大其对社区的影响。论坛焦点的角色可能在塑造公众对该事件及相关实体的看法方面具有重要意义。[数据: 关系 (40)]"


# 真实数据

使用以下文本回答。不要在回答中编造任何内容。

文本:
{input_text}

报告应包括以下部分:

- TITLE: 代表社区关键实体的社区名称 - 标题应简短但具体。尽可能在标题中包含代表性的命名实体。
- SUMMARY: 社区整体结构的执行摘要,其实体如何相互关联,以及与其实体相关的重要信息。
- IMPACT SEVERITY RATING: 一个0-10之间的浮点分数,表示社区内实体所构成影响的严重程度。IMPACT是社区的重要性评分。
- RATING EXPLANATION: 用一句话解释影响严重程度评级。
- DETAILED FINDINGS: 关于社区的5-10个关键见解列表。每个见解应有一个简短摘要,后跟多段解释性文本,根据下面的引用规则进行引用。要全面。

以格式良好的YAML格式字符串返回输出,格式如下:
    title: <报告标题>
    summary: <执行摘要>
    rating: <影响严重程度评级>
    rating_explanation: <评级解释>
    findings:
      - summary: <见解1摘要>
        explanation: <见解1解释>
      - summary: <见解2摘要>
        explanation: <见解2解释>

# 引用规则

由数据支持的要点应列出其数据引用,如下所示:

"这是一个由多个数据引用支持的示例句子[数据: <数据集名称> (记录ID); <数据集名称> (记录ID)]。"

单个引用中不要列出超过5个记录ID。而是列出最相关的5个记录ID,并添加"+更多"表示还有更多。

例如:
"人物X是公司Y的所有者,并受到许多不当行为的指控[数据: 报告 (1), 实体 (5, 7); 关系 (23); 声明 (7, 2, 34, 64, 46, +更多)]。"

其中1、5、7、23、2、34、46和64表示相关数据记录的ID(不是索引)。

不要包含没有提供支持证据的信息。

输出:"""
