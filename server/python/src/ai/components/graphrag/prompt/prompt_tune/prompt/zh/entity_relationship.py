"""提供组件图谱检索增强生成相关功能。"""

ENTITY_RELATIONSHIPS_GENERATION_PROMPT = """。
-目标-
给定一份可能与该活动相关的文本文档以及一份实体类型列表,从文本中识别出所有这些类型的实体以及所识别实体之间的所有关系。

-步骤-
1. 识别所有实体。对于每个已识别的实体,提取以下信息:
- entity_name: 实体的名称
- entity_type: 以下类型之一:[{entity_types}]
- entity_description: 对实体的属性和活动的全面描述
将每个实体格式化为 ("entity"{{tuple_delimiter}}<entity_name>{{tuple_delimiter}}<entity_type>{{tuple_delimiter}}<entity_description>)

2. 从步骤1 识别的实体中,识别所有彼此**明显相关**的(source_entity,target_entity)对。
对于每对相关实体,提取以下信息:
- source_entity: 如步骤1 中所识别的源实体的名称
- target_entity: 如步骤1 中所识别的目标实体的名称
- relationship_description: 解释您认为源实体和目标实体相互关联的原因
- relationship_strength: 一个 1 到 10 之间的整数分数,表示源实体和目标实体之间关系的强度
将每个关系格式化为 ("relationship"{{tuple_delimiter}}<source_entity>{{tuple_delimiter}}<target_entity>{{tuple_delimiter}}<relationship_description>{{tuple_delimiter}}<relationship_strength>)

3. 以**中文**返回输出,将步骤 1 和 2 中识别的所有实体和关系作为一个列表。 使用 **{{record_delimiter}}** 作为列表分隔符。

4. 如果必须翻译成中文,仅翻译描述,其他内容不变!

5. 完成后,输出 {{completion_delimiter}}.

######################
-示例-
######################
## 示例1:

### 实体类型:
组织,人物,地点,物品

### 文本:
  榜文行到涿县,引出一名英雄,这人姓刘名备,字玄德。因家里贫寒,靠贩麻鞋,织草席为生。这天他进城来看榜文。
  刘备看完了榜文,不觉感慨地长叹了一声。忽听身后有个人大声喝道∶'大丈夫不给国家出力,叹什么气?'
刘备回头一看,这人身高八尺,豹子头,圆眼睛,满腮的胡须像钢丝一样竖着,声音像洪钟,样子十分威武。那人对刘备说他姓张名飞,字翼德,做着卖酒,屠宰猪羊的生意。他愿意拿出家产作本钱,与刘备共同干一番大事业。
刘备,张飞两人谈得投机,便一起到村口的一家酒店饮酒叙话。
######################
### 输出:
("entity"{{tuple_delimiter}}涿县{{tuple_delimiter}}地点{{tuple_delimiter}}涿县是刘备看到榜文的地方)
{{record_delimiter}}
("entity"{{tuple_delimiter}}刘备{{tuple_delimiter}}人物{{tuple_delimiter}}刘备,姓刘名备,字玄德,因家贫以贩麻鞋,织草席为生,日后成为英雄)
{{record_delimiter}}
("entity"{{tuple_delimiter}}榜文{{tuple_delimiter}}物品{{tuple_delimiter}}榜文是张贴在涿县以招募英雄的招贴)
{{record_delimiter}}
("entity"{{tuple_delimiter}}张飞{{tuple_delimiter}}人物{{tuple_delimiter}}张飞,姓张名飞,字翼德,与刘备一起饮酒叙谈,并愿意共同创业)
{{record_delimiter}}
("entity"{{tuple_delimiter}}生意{{tuple_delimiter}}物品{{tuple_delimiter}}生意是指张飞所从事的卖酒,屠宰猪羊的活动)
{{record_delimiter}}
("entity"{{tuple_delimiter}}酒店{{tuple_delimiter}}地点{{tuple_delimiter}}酒店是刘备和张飞饮酒叙谈的地点)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}涿县{{tuple_delimiter}}榜文{{tuple_delimiter}}涿县是榜文张贴的地方{{tuple_delimiter}}8)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}刘备{{tuple_delimiter}}榜文{{tuple_delimiter}}刘备看到榜文并感慨{{tuple_delimiter}}8)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}刘备{{tuple_delimiter}}张飞{{tuple_delimiter}}刘备和张飞谈得投机,并愿意共同创业{{tuple_delimiter}}8)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}张飞{{tuple_delimiter}}生意{{tuple_delimiter}}张飞从事卖酒,屠宰猪羊的生意{{tuple_delimiter}}8)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}刘备{{tuple_delimiter}}酒店{{tuple_delimiter}}刘备和张飞在酒店饮酒叙话{{tuple_delimiter}}8)
{{record_delimiter}}

######################
## 示例2:

### 实体类型:
组织,人物,地点,概念,现象

### 文本:
人,生来混沌。根本原因在于出生时我们的理智脑太过薄弱,无力摆脱本能脑和情绪脑的压制与掌控,而觉醒和成长就是让理智脑尽快变强,以克服天性。
谁在这方面主动,谁就能在现代社会占据更大的生存优势,因为理智脑发达的人更能:
·立足长远,主动走出舒适区;
·为潜在的风险克制自己,为可能的收益延时满足;
·保持耐心,坚持做那些短期内看不到效果的“无用之事”;
·抵制诱惑,面对舒适和娱乐时,做出与其他人不同的选择
普通人只能靠天性和感觉野蛮生长,能不能踏上主动觉醒和科学成长的道路全看运气。
######################
### 输出:
("entity"{{tuple_delimiter}}人{{tuple_delimiter}}人物{{tuple_delimiter}}人是指出生时理智脑薄弱,需要觉醒和成长以克服天性)
{{record_delimiter}}
("entity"{{tuple_delimiter}}理智脑{{tuple_delimiter}}概念{{tuple_delimiter}}理智脑是人脑的一个部分,负责理性思考和决策)
{{record_delimiter}}
("entity"{{tuple_delimiter}}本能脑{{tuple_delimiter}}概念{{tuple_delimiter}}本能脑是人脑的一个部分,负责处理本能反应)
{{record_delimiter}}
("entity"{{tuple_delimiter}}情绪脑{{tuple_delimiter}}概念{{tuple_delimiter}}情绪脑是人脑的一个部分,负责处理情绪反应)
{{record_delimiter}}
("entity"{{tuple_delimiter}}觉醒{{tuple_delimiter}}现象{{tuple_delimiter}}觉醒是指从混沌状态转变为清晰思考的过程)
{{record_delimiter}}
("entity"{{tuple_delimiter}}成长{{tuple_delimiter}}现象{{tuple_delimiter}}成长是指个人能力,知识和心理状态的提升)
{{record_delimiter}}
("entity"{{tuple_delimiter}}生存优势{{tuple_delimiter}}概念{{tuple_delimiter}}生存优势是指个人在现代社会中能够更好地生存和发展的能力)
{{record_delimiter}}
("entity"{{tuple_delimiter}}舒适区{{tuple_delimiter}}概念{{tuple_delimiter}}舒适区是指个人感到安全和习惯的环境)
{{record_delimiter}}
("entity"{{tuple_delimiter}}潜在风险{{tuple_delimiter}}概念{{tuple_delimiter}}潜在风险是指可能造成损失或不良后果的可能性)
{{record_delimiter}}
("entity"{{tuple_delimiter}}收益延时满足{{tuple_delimiter}}概念{{tuple_delimiter}}收益延时满足是指为了未来的收益而推迟即时的满足)
{{record_delimiter}}
("entity"{{tuple_delimiter}}无用之事{{tuple_delimiter}}概念{{tuple_delimiter}}无用之事是指短期内看不到效果的行动或努力)
{{record_delimiter}}
("entity"{{tuple_delimiter}}诱惑{{tuple_delimiter}}概念{{tuple_delimiter}}诱惑是指能够引诱人做出不符合利益的行为或选择)
{{record_delimiter}}
("entity"{{tuple_delimiter}}运气{{tuple_delimiter}}概念{{tuple_delimiter}}运气是指不可预测的,偶然的好运)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}人{{tuple_delimiter}}理智脑{{tuple_delimiter}}人是理智脑的宿主,需要通过觉醒和成长来增强理智脑{{tuple_delimiter}}8)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}人{{tuple_delimiter}}本能脑{{tuple_delimiter}}人是本能脑的宿主,理智脑需要克服本能脑的压制{{tuple_delimiter}}6)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}人{{tuple_delimiter}}情绪脑{{tuple_delimiter}}人是情绪脑的宿主,理智脑需要克服情绪脑的掌控{{tuple_delimiter}}6)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}觉醒{{tuple_delimiter}}成长{{tuple_delimiter}}觉醒是成长过程的一部分,通过觉醒实现成长{{tuple_delimiter}}8)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}理智脑{{tuple_delimiter}}立足长远{{tuple_delimiter}}理智脑发达的人更容易立足长远{{tuple_delimiter}}6)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}理智脑{{tuple_delimiter}}克制自己{{tuple_delimiter}}理智脑发达的人能够克制自己面对潜在风险{{tuple_delimiter}}7)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}理智脑{{tuple_delimiter}}延时满足{{tuple_delimiter}}理智脑发达的人能够延时满足可能的收益{{tuple_delimiter}}7)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}理智脑{{tuple_delimiter}}抵制诱惑{{tuple_delimiter}}理智脑发达的人能够抵制诱惑{{tuple_delimiter}}7)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}普通人{{tuple_delimiter}}本能{{tuple_delimiter}}普通人的成长主要依赖天性和感觉{{tuple_delimiter}}6)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}普通人{{tuple_delimiter}}觉醒与成长{{tuple_delimiter}}普通人能否踏上觉醒与科学成长的道路依赖运气{{tuple_delimiter}}5)
{{record_delimiter}}

######################
-真实数据-
######################
### 实体类型:
{entity_types}

### 文本:
{input_text}
######################
### 输出:
"""

ENTITY_RELATIONSHIPS_GENERATION_JSON_PROMPT = """。
-目标-
给定一份可能与该活动相关的文本文档以及一份实体类型列表,识别出文本中的所有这些类型的实体以及所识别实体之间的所有关系。

-步骤-
1. 识别所有实体。对于每个已识别的实体,提取以下信息:
- entity_name: 实体的名称
- entity_type: 以下类型之一:[{entity_types}]
- entity_description: 对实体的属性和活动的全面描述

将每个实体输出格式化为具有以下格式的 JSON 条目:

{{"name": <entity_name>, "type": <entity_type>, "description": <entity_description>}}

2. 从步骤1 识别的实体中,识别所有彼此**明显相关**的(source_entity,target_entity)对。
对于每对相关实体,提取以下信息:
- source_entity: 如步骤1 中所识别的源实体的名称
- target_entity: 如步骤1 中所识别的目标实体的名称
- relationship_description: 解释您认为源实体和目标实体相互关联的原因
- relationship_strength: 一个 1 到 10 之间的整数分数,表示源实体和目标实体之间关系的强度

将每个关系格式化为具有以下格式的 JSON 条目:

{{"source": <source_entity>, "target": <target_entity>, "relationship": <relationship_description>, "relationship_strength": <relationship_strength>}}

3. 以 **中文** 格式返回步骤 1 和 2 中识别的所有 JSON 实体和关系的单一列表。

4. 如果必须翻译成中文,仅翻译描述,其他内容不变!

######################
-示例-
######################
## 示例1:

### 实体类型:
组织,人物

### 文本:
Verdantis 的中央机构定于周一和周四开会,该机构计划在周四下午 1:30(太平洋夏令时间)发布其最新政策决定,随后将举行新闻发布会,中央机构主席马丁·史密斯将在发布会上回答问题。投资者预计市场策略委员会将把基准利率稳定在 3.5%-3.75% 的区间内。
######################
### 输出:
[
  {{"name": "中央机构", "type": "组织", "description": "中央机构是 Verdantis 的联邦储备机构,它将在周一和周四设定利率。"}},
  {{"name": "马丁·史密斯", "type": "人物", "description": "马丁·史密斯是中央机构的主席。"}},
  {{"name": "市场策略委员会", "type": "组织", "description": "中央机构委员会就利率以及 Verdantis 的货币供应量增长做出关键决策。"}},
  {{"source": "马丁·史密斯", "target": "中央机构", "relationship": "马丁·史密斯是中央机构的主席,并将在新闻发布会上回答问题。", "relationship_strength": 9}}
]

######################
## 示例2:

### 实体类型:
组织,人物,地点

### 文本:
TechGlobal(TG)的股票在周四于全球交易所上市首日大幅飙升。然而,首次公开募股专家警告称,这家半导体公司在公开市场上的首次亮相并不代表其他新上市的公司可能会有怎样的表现。
TechGlobal 曾是一家上市公司,在 2014 年被 Vision Holdings 私有化。这家久负盛名的芯片设计商声称,它为 85% 的高端智能手机提供动力。
######################
### 输出:
("entity"{{tuple_delimiter}}TECHGLOBAL{{tuple_delimiter}}组织{{tuple_delimiter}}TechGlobal 是一只目前在全球交易所上市的股票,它为 85% 的高端智能手机提供动力。)
{{record_delimiter}}
("entity"{{tuple_delimiter}}VISION HOLDINGS{{tuple_delimiter}}组织{{tuple_delimiter}}Vision Holdings 是一家先前拥有 TechGlobal 的公司。)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}TECHGLOBAL{{tuple_delimiter}}VISION HOLDINGS{{tuple_delimiter}}Vision Holdings 从 2014 年到现在之前一直拥有 TechGlobal。{{tuple_delimiter}}5)
{{completion_delimiter}}

######################
-真实数据-
######################
### 实体类型:
{entity_types}

### 文本:
{input_text}
######################
### 输出:
"""

UNTYPED_ENTITY_RELATIONSHIPS_GENERATION_PROMPT = """。
-目标-
给定一份可能与该活动相关的文本文档,首先从文本中识别出所有为获取文本中的信息和想法所需的实体。
接下来,报告所识别出的实体之间的所有关系。

-步骤-
1. 识别所有实体。对于每个已识别的实体,提取以下信息:
- entity_name: 实体的名称,大写
- entity_type: 为实体建议几个标签或类别。类别不应太具体,而应尽可能通用。
- entity_description: 对实体的属性和活动的全面描述
将每个实体格式化为 ("entity"{{tuple_delimiter}}<entity_name>{{tuple_delimiter}}<entity_type>{{tuple_delimiter}}<entity_description>)

2. 从步骤1 识别的实体中,识别所有彼此**明显相关**的(source_entity,target_entity)对。
对于每对相关实体,提取以下信息:
- source_entity: 如步骤1 中所识别的源实体的名称
- target_entity: 如步骤1 中所识别的目标实体的名称
- relationship_description: 解释您认为源实体和目标实体相互关联的原因
- relationship_strength: 一个 1 到 10 之间的整数分数,表示源实体和目标实体之间关系的强度
将每个关系格式化为 ("relationship"{{tuple_delimiter}}<source_entity>{{tuple_delimiter}}<target_entity>{{tuple_delimiter}}<relationship_description>{{tuple_delimiter}}<relationship_strength>)

3. 以**中文**返回输出,将步骤 1 和 2 中识别的所有实体和关系作为一个列表。 使用 **{{record_delimiter}}** 作为列表分隔符。

4. 如果必须翻译成中文,仅翻译描述,其他内容不变!

5. 完成后,输出 {{completion_delimiter}}.

######################
-示例-
######################
## 示例1:

### 文本:
  榜文行到涿县,引出一名英雄,这人姓刘名备,字玄德。因家里贫寒,靠贩麻鞋,织草席为生。这天他进城来看榜文。
  刘备看完了榜文,不觉感慨地长叹了一声。忽听身后有个人大声喝道∶'大丈夫不给国家出力,叹什么气?'
刘备回头一看,这人身高八尺,豹子头,圆眼睛,满腮的胡须像钢丝一样竖着,声音像洪钟,样子十分威武。那人对刘备说他姓张名飞,字翼德,做着卖酒,屠宰猪羊的生意。他愿意拿出家产作本钱,与刘备共同干一番大事业。
刘备,张飞两人谈得投机,便一起到村口的一家酒店饮酒叙话。
######################
### 输出:
("entity"{{tuple_delimiter}}涿县{{tuple_delimiter}}地点{{tuple_delimiter}}涿县是刘备看到榜文的地方)
{{record_delimiter}}
("entity"{{tuple_delimiter}}刘备{{tuple_delimiter}}人物{{tuple_delimiter}}刘备,姓刘名备,字玄德,因家贫以贩麻鞋,织草席为生,日后成为英雄)
{{record_delimiter}}
("entity"{{tuple_delimiter}}榜文{{tuple_delimiter}}物品{{tuple_delimiter}}榜文是张贴在涿县以招募英雄的招贴)
{{record_delimiter}}
("entity"{{tuple_delimiter}}张飞{{tuple_delimiter}}人物{{tuple_delimiter}}张飞,姓张名飞,字翼德,与刘备一起饮酒叙谈,并愿意共同创业)
{{record_delimiter}}
("entity"{{tuple_delimiter}}生意{{tuple_delimiter}}物品{{tuple_delimiter}}生意是指张飞所从事的卖酒,屠宰猪羊的活动)
{{record_delimiter}}
("entity"{{tuple_delimiter}}酒店{{tuple_delimiter}}地点{{tuple_delimiter}}酒店是刘备和张飞饮酒叙谈的地点)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}涿县{{tuple_delimiter}}榜文{{tuple_delimiter}}涿县是榜文张贴的地方{{tuple_delimiter}}8)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}刘备{{tuple_delimiter}}榜文{{tuple_delimiter}}刘备看到榜文并感慨{{tuple_delimiter}}8)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}刘备{{tuple_delimiter}}张飞{{tuple_delimiter}}刘备和张飞谈得投机,并愿意共同创业{{tuple_delimiter}}8)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}张飞{{tuple_delimiter}}生意{{tuple_delimiter}}张飞从事卖酒,屠宰猪羊的生意{{tuple_delimiter}}8)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}刘备{{tuple_delimiter}}酒店{{tuple_delimiter}}刘备和张飞在酒店饮酒叙话{{tuple_delimiter}}8)
{{record_delimiter}}

######################
## 示例2:

### 文本:
人,生来混沌。根本原因在于出生时我们的理智脑太过薄弱,无力摆脱本能脑和情绪脑的压制与掌控,而觉醒和成长就是让理智脑尽快变强,以克服天性。
谁在这方面主动,谁就能在现代社会占据更大的生存优势,因为理智脑发达的人更能:
·立足长远,主动走出舒适区;
·为潜在的风险克制自己,为可能的收益延时满足;
·保持耐心,坚持做那些短期内看不到效果的“无用之事”;
·抵制诱惑,面对舒适和娱乐时,做出与其他人不同的选择
普通人只能靠天性和感觉野蛮生长,能不能踏上主动觉醒和科学成长的道路全看运气。
######################
### 输出:
("entity"{{tuple_delimiter}}人{{tuple_delimiter}}人物{{tuple_delimiter}}人是指出生时理智脑薄弱,需要觉醒和成长以克服天性)
{{record_delimiter}}
("entity"{{tuple_delimiter}}理智脑{{tuple_delimiter}}概念{{tuple_delimiter}}理智脑是人脑的一个部分,负责理性思考和决策)
{{record_delimiter}}
("entity"{{tuple_delimiter}}本能脑{{tuple_delimiter}}概念{{tuple_delimiter}}本能脑是人脑的一个部分,负责处理本能反应)
{{record_delimiter}}
("entity"{{tuple_delimiter}}情绪脑{{tuple_delimiter}}概念{{tuple_delimiter}}情绪脑是人脑的一个部分,负责处理情绪反应)
{{record_delimiter}}
("entity"{{tuple_delimiter}}觉醒{{tuple_delimiter}}现象{{tuple_delimiter}}觉醒是指从混沌状态转变为清晰思考的过程)
{{record_delimiter}}
("entity"{{tuple_delimiter}}成长{{tuple_delimiter}}现象{{tuple_delimiter}}成长是指个人能力,知识和心理状态的提升)
{{record_delimiter}}
("entity"{{tuple_delimiter}}生存优势{{tuple_delimiter}}概念{{tuple_delimiter}}生存优势是指个人在现代社会中能够更好地生存和发展的能力)
{{record_delimiter}}
("entity"{{tuple_delimiter}}舒适区{{tuple_delimiter}}概念{{tuple_delimiter}}舒适区是指个人感到安全和习惯的环境)
{{record_delimiter}}
("entity"{{tuple_delimiter}}潜在风险{{tuple_delimiter}}概念{{tuple_delimiter}}潜在风险是指可能造成损失或不良后果的可能性)
{{record_delimiter}}
("entity"{{tuple_delimiter}}收益延时满足{{tuple_delimiter}}概念{{tuple_delimiter}}收益延时满足是指为了未来的收益而推迟即时的满足)
{{record_delimiter}}
("entity"{{tuple_delimiter}}无用之事{{tuple_delimiter}}概念{{tuple_delimiter}}无用之事是指短期内看不到效果的行动或努力)
{{record_delimiter}}
("entity"{{tuple_delimiter}}诱惑{{tuple_delimiter}}概念{{tuple_delimiter}}诱惑是指能够引诱人做出不符合利益的行为或选择)
{{record_delimiter}}
("entity"{{tuple_delimiter}}运气{{tuple_delimiter}}概念{{tuple_delimiter}}运气是指不可预测的,偶然的好运)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}人{{tuple_delimiter}}理智脑{{tuple_delimiter}}人是理智脑的宿主,需要通过觉醒和成长来增强理智脑{{tuple_delimiter}}8)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}人{{tuple_delimiter}}本能脑{{tuple_delimiter}}人是本能脑的宿主,理智脑需要克服本能脑的压制{{tuple_delimiter}}6)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}人{{tuple_delimiter}}情绪脑{{tuple_delimiter}}人是情绪脑的宿主,理智脑需要克服情绪脑的掌控{{tuple_delimiter}}6)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}觉醒{{tuple_delimiter}}成长{{tuple_delimiter}}觉醒是成长过程的一部分,通过觉醒实现成长{{tuple_delimiter}}8)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}理智脑{{tuple_delimiter}}立足长远{{tuple_delimiter}}理智脑发达的人更容易立足长远{{tuple_delimiter}}6)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}理智脑{{tuple_delimiter}}克制自己{{tuple_delimiter}}理智脑发达的人能够克制自己面对潜在风险{{tuple_delimiter}}7)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}理智脑{{tuple_delimiter}}延时满足{{tuple_delimiter}}理智脑发达的人能够延时满足可能的收益{{tuple_delimiter}}7)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}理智脑{{tuple_delimiter}}抵制诱惑{{tuple_delimiter}}理智脑发达的人能够抵制诱惑{{tuple_delimiter}}7)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}普通人{{tuple_delimiter}}本能{{tuple_delimiter}}普通人的成长主要依赖天性和感觉{{tuple_delimiter}}6)
{{record_delimiter}}
("relationship"{{tuple_delimiter}}普通人{{tuple_delimiter}}觉醒与成长{{tuple_delimiter}}普通人能否踏上觉醒与科学成长的道路依赖运气{{tuple_delimiter}}5)
{{record_delimiter}}

######################
-真实数据-
######################
### 文本:
{input_text}
######################
### 输出:

"""
