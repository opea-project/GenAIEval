import argparse
import concurrent.futures
import json
import random
import time
import msgspec
import numpy
import requests
#from transformers import AutoModelForCausalLM, AutoTokenizer

# tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2-7B-Instruct")

query_128 = "In a world where technology has advanced beyond our wildest dreams, humanity stands on the brink of a new era. The year is 2050, and artificial intelligence has become an integral part of everyday life. Autonomous vehicles zip through the streets, drones deliver packages with pinpoint accuracy, and smart homes anticipate every need of their inhabitants. But with these advancements come new challenges and ethical dilemmas. As society grapples with the implications of AI, questions about privacy, security, and the nature of consciousness itself come to the forefront. Amidst this backdrop, a new breakthrough in quantum computing promises to revolutionize the field even further."

query_128_zh = "请为我总结以下内容：在古老的东方，有一个神秘而美丽的国家，这里有着悠久的历史和丰富的文化。国家的山川河流孕育了智慧勤劳的人民，他们用双手和智慧创造了辉煌的文明。古老的城市保存着许多历史悠久的建筑和文物，展现了国家的辉煌历史。在这个国家，人们热爱生活，追求幸福，传统节日里欢聚一堂，共享美好时光。这里的教育传统深厚，科技发展迅猛，人民努力追求卓越，文化和美食也非常独特。国家的自然风光和科技进步都引人注目。请详细地总结这些信息的主要内容项。"

prompt_2k = """
### 你将扮演一个乐于助人、尊重他人并诚实的助手，你的目标是帮助用户解答问题。有效地利用来自本地知识库的搜索结果。确保你的回答中只包含相关信息。如果你不确定问题的答案，请避免分享不准确的信息。
### 搜索结果：在遥远的东方，有一个古老而神秘的国家，这个国家有着悠久的历史和丰富的文化。这里的山川河流孕育了无数代勤劳智慧的人民，他们用自己的双手和智慧创造了辉煌的文明。在这片土地上，有着许多美丽的传说和动人的故事。相传很久以前，这里住着一个年轻的樵夫，他每天都到深山里砍柴，虽然生活艰辛，但他始终保持着乐观的态度。一天，樵夫在山中偶然发现了一棵长满奇异果实的树，他小心翼翼地摘下一个果子，尝了一口，顿时感到浑身充满了力量。从那天起，他的生活发生了巨大的变化。这个国家不仅有美丽的自然风光，还有丰富的文化遗产。古老的城市中，保存着许多历史悠久的建筑和文物，它们见证了这个国家的辉煌历史。在这里，你可以看到雄伟的宫殿、精致的园林和宏伟的庙宇，每一处都散发着浓厚的历史气息。走在古老的街道上，仿佛能够听到历史的回声，感受到古人的智慧和创造力。这个国家的人们勤劳勇敢，善良友爱。他们热爱生活，追求幸福。无论是丰收的季节，还是节日的庆典，人们总是欢聚一堂，尽情享受美好的时光。传统的节日里，人们穿上节日的盛装，载歌载舞，互相祝福，分享美食。特别是春节，这是这个国家最重要的节日，家家户户都会张灯结彩，迎接新年的到来。孩子们最喜欢这个时候，因为他们可以收到长辈们的红包，穿上新衣服，吃到各种美味的年货。这个国家还有着深厚的教育传统。古代的学者们孜孜不倦地追求知识，他们留下了许多宝贵的文献和著作，对后世产生了深远的影响。如今，这里的学校和大学依然是培养人才的摇篮，许多年轻人怀揣着梦想，努力学习，期望将来能够为国家和社会做出贡献。科学技术的飞速发展，也为这个国家带来了新的机遇和挑战。人们不断创新，追求卓越，力争在国际舞台上占据一席之地。这个国家的美食也是一大特色。无论是南方的清淡口味，还是北方的浓郁口感，都能找到独特的风味。街头巷尾的小吃摊，饭馆里的家常菜，无不让人垂涎欲滴。特别是火锅，作为这里的代表性美食，深受人们的喜爱。无论寒冬腊月，还是炎炎夏日，围坐在火锅旁，大家一起涮菜，一起聊天，其乐融融。在这个国家的广袤大地上，还有许多值得探索的地方。壮丽的高山、广袤的草原、秀美的江南水乡，每一处都让人流连忘返。探寻自然的奥秘，感受大自然的神奇，是许多人心中的梦想。无论是徒步旅行，还是自驾游，都能在这里找到属于自己的乐趣。这个国家的科技发展也令人瞩目。从古代的四大发明到现代的高科技产业，这里的科技进步始终走在世界前列。许多科技公司和研究机构在这里落户，吸引了大量的科技人才。创新和研发成为推动经济发展的重要力量。尤其是在人工智能、量子计算、生物技术等领域，这个国家取得了显著的成就，为全球科技进步贡献了自己的力量。这个国家的人民非常注重教育和文化传承。从小，孩子们就被教导要尊重知识，热爱学习。学校教育不仅关注学术成绩，还注重培养学生的综合素质和创新能力。各种文化活动和社会实践让学生们在学习的同时，了解社会，增长见识。这个国家的图书馆、博物馆和文化中心遍布各地，为人们提供了丰富的文化资源和学习机会。这个国家的艺术和文学也具有独特的魅力。古代的诗人和画家留下了许多不朽的作品，现代的艺术家们则不断探索新的表现形式和创作方法。无论是传统的书法绘画，还是现代的电影音乐，都展现出这个国家深厚的文化底蕴和创新精神。每年，这里都会举办各种艺术节和文化展览，吸引了大批艺术爱好者和游客。这个国家的体育事业也蓬勃发展。无论是传统的武术，还是现代的竞技体育，都有着广泛的群众基础。每当有大型体育赛事，人们都会热情地支持自己的运动员，为他们加油助威。这个国家的运动员们在国际比赛中屡创佳绩，为国家争光。体育不仅是强身健体的方式，也是增进友谊和团结的纽带。总之，这个古老而又充满活力的国家，正以崭新的姿态走向未来。她的人民团结一心，勇往直前，为实现梦想而努力奋斗。每一个人都是这个国家的一部分，每一个梦想都值得被尊重和珍惜。未来的路还很长，但只要大家携手并进，就一定能够迎来更加美好的明天。在这片充满希望的土地上，还有许多未被发掘的宝藏等待着人们去发现。历史的长河流淌不息，新时代的篇章也在不断书写。这个国家的人民用他们的智慧和双手，创造着一个又一个奇迹。无论是科技的突破，还是文化的传承，每一个领域都在焕发着新的活力。每一位平凡的劳动者，每一位辛勤的学者，每一位勇敢的创新者，都是这个国家走向繁荣与强大的基石。在这片土地上，人们懂得感恩与珍惜。他们感恩祖先留下的宝贵遗产，珍惜现在所拥有的一切。无论生活多么忙碌，人们总会抽出时间，陪伴家人，朋友，共同度过那些美好时光。家庭的温暖，友情的珍贵，这些都是人生中最宝贵的财富。面对未来，这个国家的人民充满信心。他们深知，只有团结一致，才能克服一切困难。无论前方的路多么崎岖，只要大家心往一处想，劲往一处使，就一定能够迎来光明的明天。每一个人的梦想，都是这个国家梦想的一部分。每一个人的努力，都是这个国家前进的动力。无论身处何地，心系祖国，这份情感，永不改变。这个国家的故事还在继续，每一天都是新的篇章。未来的道路上，充满了无限的可能。这个国家的人民，将继续用他们的智慧和努力，书写更加辉煌的历史。无论风雨，始终前行，因为他们相信，光明就在前方，梦想终会实现。在这片充满希望的土地上，还有许多未被发掘的宝藏等待着人们去发现。历史的长河流淌不息，新时代的篇章也在不断书写。这个国家的人民用他们的智慧和双手，创造着一个又一个奇迹。无论是科技的突破，还是文化的传承，每一个领域都在焕发着新的活力。每一位平凡的劳动者，每一位辛勤的学者，每一位勇敢的创新者，都是这个国家走向繁荣与强大的基石。在这片土地上，人们懂得感恩与珍惜。他们感恩祖先留下的宝贵遗产，珍惜现在所拥有的一切。无论生活多么忙碌，人们总会抽出时间，陪伴家人，朋友，共同度过那些美好时光。家庭的温暖，友情的珍贵，这些都是人生中最宝贵的财富。面对未来，这个国家的人民充满信心。他们深知，只有团结一致，才能克服一切困难。无论前方的路多么崎岖，只要大家心往一处想，劲往一处使，就一定能够迎来光明的明天。每一个人的梦想，都是这个国家梦想的一部分。每一个人的努力，都是这个国家前进的动力。无论身处何地，心系祖国，这份情感，永不改变。这个国家的故事还在继续，每一天都是新的篇章。未来的道路上，充满了无限的可能。这个国家的人民，将继续用他们的智慧和努力，书写更加辉煌的历史。无论风雨，始终前行，因为他们相信，光明就在前方，梦想终会实现。这个国家的艺术和文化也在不断发展。传统与现代在这里交融，古老的技艺与新的创意相得益彰。无论是传统的书法绘画，还是现代的电影音乐，这里都有无数的艺术瑰宝等待人们去发现和欣赏。艺术节、文化展览遍布全国，每一处都吸引着大量的游客和艺术爱好者。这里的博物馆收藏了无数珍贵的文物，展示了这个国家丰富的历史和文化。体育也是这个国家人民生活中不可或缺的一部分。每到大型体育赛事，举国上下都充满了激情和活力。运动员们用他们的拼搏精神和优异成绩，为国家赢得了无数荣誉。无论是传统的武术，还是现代的竞技体育，都有着广泛的群众基础。体育不仅是强身健体的方式，也是增进友谊和团结的纽带。这个国家的科技发展也是全球瞩目的。人工智能、量子计算、生物技术等领域，这个国家的研究机构和企业都取得了显著的成就。许多科技公司在国际上享有盛誉，吸引了大量的科技人才前来创业和工作。创新和研发成为推动经济发展的重要力量。教育也是这个国家的优先发展领域。从幼儿园到大学，教育体系不断完善，为每一个孩子提供了公平的教育机会。学校不仅关注学生的学术成绩，还注重他们的综合素质和创新能力的培养。各种课外活动和社会实践让学生们在学习的同时，了解社会，增长见识。教育的不断进步，为国家的发展提供了源源不断的人才支持。旅游业也是这个国家的重要产业。这里有壮丽的自然景观和丰富的人文景观，每年吸引着大量的游客前来观光。无论是高山、草原、湖泊，还是古城、庙宇、园林，每一处都让人流连忘返。探寻自然的奥秘，感受历史的厚重，是许多人心中的梦想。这个国家的农业也在不断现代化。通过科技的应用，农业生产效率大大提高，农民的生活水平也得到了显著改善。绿色农业和有机农业的发展，不仅保护了环境，也为人们提供了健康的食品。农村的基础设施建设也在不断推进，乡村旅游成为新的经济增长点。在这个国家的每一个角落，人们都在为美好的生活而努力奋斗。无论是城市还是乡村，每一个地方都焕发着新的生机。真棒。
### 问题：请总结这篇文章。
### 回答：
"""

prompt_3k = """
### 你将扮演一个乐于助人、尊重他人并诚实的助手，你的目标是帮助用户解答问题。有效地利用来自本地知识库的搜索结果。确保你的回答中只包含相关信息。如果你不确定问题的答案，请避免分享不准确的信息。
### 搜索结果：在遥远的东方，有一个古老而神秘的国家，这个国家有着悠久的历史和丰富的文化。这里的山川河流孕育了无数代勤劳智慧的人民，他们用自己的双手和智慧创造了辉煌的文明。在这片土地上，有着许多美丽的传说和动人的故事。相传很久以前，这里住着一个年轻的樵夫，他每天都到深山里砍柴，虽然生活艰辛，但他始终保持着乐观的态度。一天，樵夫在山中偶然发现了一棵长满奇异果实的树，他小心翼翼地摘下一个果子，尝了一口，顿时感到浑身充满了力量。从那天起，他的生活发生了巨大的变化。这个国家不仅有美丽的自然风光，还有丰富的文化遗产。古老的城市中，保存着许多历史悠久的建筑和文物，它们见证了这个国家的辉煌历史。在这里，你可以看到雄伟的宫殿、精致的园林和宏伟的庙宇，每一处都散发着浓厚的历史气息。走在古老的街道上，仿佛能够听到历史的回声，感受到古人的智慧和创造力。这个国家的人们勤劳勇敢，善良友爱。他们热爱生活，追求幸福。无论是丰收的季节，还是节日的庆典，人们总是欢聚一堂，尽情享受美好的时光。传统的节日里，人们穿上节日的盛装，载歌载舞，互相祝福，分享美食。特别是春节，这是这个国家最重要的节日，家家户户都会张灯结彩，迎接新年的到来。孩子们最喜欢这个时候，因为他们可以收到长辈们的红包，穿上新衣服，吃到各种美味的年货。这个国家还有着深厚的教育传统。古代的学者们孜孜不倦地追求知识，他们留下了许多宝贵的文献和著作，对后世产生了深远的影响。如今，这里的学校和大学依然是培养人才的摇篮，许多年轻人怀揣着梦想，努力学习，期望将来能够为国家和社会做出贡献。科学技术的飞速发展，也为这个国家带来了新的机遇和挑战。人们不断创新，追求卓越，力争在国际舞台上占据一席之地。这个国家的美食也是一大特色。无论是南方的清淡口味，还是北方的浓郁口感，都能找到独特的风味。街头巷尾的小吃摊，饭馆里的家常菜，无不让人垂涎欲滴。特别是火锅，作为这里的代表性美食，深受人们的喜爱。无论寒冬腊月，还是炎炎夏日，围坐在火锅旁，大家一起涮菜，一起聊天，其乐融融。在这个国家的广袤大地上，还有许多值得探索的地方。壮丽的高山、广袤的草原、秀美的江南水乡，每一处都让人流连忘返。探寻自然的奥秘，感受大自然的神奇，是许多人心中的梦想。无论是徒步旅行，还是自驾游，都能在这里找到属于自己的乐趣。这个国家的科技发展也令人瞩目。从古代的四大发明到现代的高科技产业，这里的科技进步始终走在世界前列。许多科技公司和研究机构在这里落户，吸引了大量的科技人才。创新和研发成为推动经济发展的重要力量。尤其是在人工智能、量子计算、生物技术等领域，这个国家取得了显著的成就，为全球科技进步贡献了自己的力量。这个国家的人民非常注重教育和文化传承。从小，孩子们就被教导要尊重知识，热爱学习。学校教育不仅关注学术成绩，还注重培养学生的综合素质和创新能力。各种文化活动和社会实践让学生们在学习的同时，了解社会，增长见识。这个国家的图书馆、博物馆和文化中心遍布各地，为人们提供了丰富的文化资源和学习机会。这个国家的艺术和文学也具有独特的魅力。古代的诗人和画家留下了许多不朽的作品，现代的艺术家们则不断探索新的表现形式和创作方法。无论是传统的书法绘画，还是现代的电影音乐，都展现出这个国家深厚的文化底蕴和创新精神。每年，这里都会举办各种艺术节和文化展览，吸引了大批艺术爱好者和游客。这个国家的体育事业也蓬勃发展。无论是传统的武术，还是现代的竞技体育，都有着广泛的群众基础。每当有大型体育赛事，人们都会热情地支持自己的运动员，为他们加油助威。这个国家的运动员们在国际比赛中屡创佳绩，为国家争光。体育不仅是强身健体的方式，也是增进友谊和团结的纽带。总之，这个古老而又充满活力的国家，正以崭新的姿态走向未来。她的人民团结一心，勇往直前，为实现梦想而努力奋斗。每一个人都是这个国家的一部分，每一个梦想都值得被尊重和珍惜。未来的路还很长，但只要大家携手并进，就一定能够迎来更加美好的明天。在这片充满希望的土地上，还有许多未被发掘的宝藏等待着人们去发现。历史的长河流淌不息，新时代的篇章也在不断书写。这个国家的人民用他们的智慧和双手，创造着一个又一个奇迹。无论是科技的突破，还是文化的传承，每一个领域都在焕发着新的活力。每一位平凡的劳动者，每一位辛勤的学者，每一位勇敢的创新者，都是这个国家走向繁荣与强大的基石。在这片土地上，人们懂得感恩与珍惜。他们感恩祖先留下的宝贵遗产，珍惜现在所拥有的一切。无论生活多么忙碌，人们总会抽出时间，陪伴家人，朋友，共同度过那些美好时光。家庭的温暖，友情的珍贵，这些都是人生中最宝贵的财富。面对未来，这个国家的人民充满信心。他们深知，只有团结一致，才能克服一切困难。无论前方的路多么崎岖，只要大家心往一处想，劲往一处使，就一定能够迎来光明的明天。每一个人的梦想，都是这个国家梦想的一部分。每一个人的努力，都是这个国家前进的动力。无论身处何地，心系祖国，这份情感，永不改变。这个国家的故事还在继续，每一天都是新的篇章。未来的道路上，充满了无限的可能。这个国家的人民，将继续用他们的智慧和努力，书写更加辉煌的历史。无论风雨，始终前行，因为他们相信，光明就在前方，梦想终会实现。在这片充满希望的土地上，还有许多未被发掘的宝藏等待着人们去发现。历史的长河流淌不息，新时代的篇章也在不断书写。这个国家的人民用他们的智慧和双手，创造着一个又一个奇迹。无论是科技的突破，还是文化的传承，每一个领域都在焕发着新的活力。每一位平凡的劳动者，每一位辛勤的学者，每一位勇敢的创新者，都是这个国家走向繁荣与强大的基石。在这片土地上，人们懂得感恩与珍惜。他们感恩祖先留下的宝贵遗产，珍惜现在所拥有的一切。无论生活多么忙碌，人们总会抽出时间，陪伴家人，朋友，共同度过那些美好时光。家庭的温暖，友情的珍贵，这些都是人生中最宝贵的财富。面对未来，这个国家的人民充满信心。他们深知，只有团结一致，才能克服一切困难。无论前方的路多么崎岖，只要大家心往一处想，劲往一处使，就一定能够迎来光明的明天。每一个人的梦想，都是这个国家梦想的一部分。每一个人的努力，都是这个国家前进的动力。无论身处何地，心系祖国，这份情感，永不改变。这个国家的故事还在继续，每一天都是新的篇章。未来的道路上，充满了无限的可能。这个国家的人民，将继续用他们的智慧和努力，书写更加辉煌的历史。无论风雨，始终前行，因为他们相信，光明就在前方，梦想终会实现。这个国家的艺术和文化也在不断发展。传统与现代在这里交融，古老的技艺与新的创意相得益彰。无论是传统的书法绘画，还是现代的电影音乐，这里都有无数的艺术瑰宝等待人们去发现和欣赏。艺术节、文化展览遍布全国，每一处都吸引着大量的游客和艺术爱好者。这里的博物馆收藏了无数珍贵的文物，展示了这个国家丰富的历史和文化。体育也是这个国家人民生活中不可或缺的一部分。每到大型体育赛事，举国上下都充满了激情和活力。运动员们用他们的拼搏精神和优异成绩，为国家赢得了无数荣誉。无论是传统的武术，还是现代的竞技体育，都有着广泛的群众基础。体育不仅是强身健体的方式，也是增进友谊和团结的纽带。这个国家的科技发展也是全球瞩目的。人工智能、量子计算、生物技术等领域，这个国家的研究机构和企业都取得了显著的成就。许多科技公司在国际上享有盛誉，吸引了大量的科技人才前来创业和工作。创新和研发成为推动经济发展的重要力量。教育也是这个国家的优先发展领域。从幼儿园到大学，教育体系不断完善，为每一个孩子提供了公平的教育机会。学校不仅关注学生的学术成绩，还注重他们的综合素质和创新能力的培养。各种课外活动和社会实践让学生们在学习的同时，了解社会，增长见识。教育的不断进步，为国家的发展提供了源源不断的人才支持。旅游业也是这个国家的重要产业。这里有壮丽的自然景观和丰富的人文景观，每年吸引着大量的游客前来观光。无论是高山、草原、湖泊，还是古城、庙宇、园林，每一处都让人流连忘返。探寻自然的奥秘，感受历史的厚重，是许多人心中的梦想。这个国家的农业也在不断现代化。通过科技的应用，农业生产效率大大提高，农民的生活水平也得到了显著改善。绿色农业和有机农业的发展，不仅保护了环境，也为人们提供了健康的食品。农村的基础设施建设也在不断推进，乡村旅游成为新的经济增长点。在这个国家的每一个角落，人们都在为美好的生活而努力奋斗。无论是城市还是乡村，每一个地方都焕发着新的生机。政府的政策支持和人民的共同努力，让这个国家不断向前发展。未来，这个国家将继续保持开放与包容，吸引更多的人才和资源，推动经济和社会的全面进步。这个国家的历史悠久而丰富，跨越了数千年的风风雨雨。从古代的封建社会到现代的民主制度，这里的历史发展经历了许多波折和变迁。每一个历史时期都留下了深刻的印记，塑造了今天这个国家的面貌。古代的帝国、王朝和 dynasties 都在这里留下了丰 富的文化遗产，今天的人们仍然能够从这些历史遗迹中感受到当时的辉煌与荣耀。古老的皇宫、寺庙和城堡，每一处都讲述着一段段动人的历史故事。现代化进程中，这个国家也经历了巨大的变革。工业化和城市化的快速发展改变了人们的生活方式，也带来了许多新的挑战。传统的农业社会逐渐转变为现代化的工业社会，科技和经济的发展推动了社会的进步。高楼大厦、繁忙的街道和现代化的交通系统，都展示了这个国家的蓬勃发展和强大实力。在这些变化中，人们不断调整自己的生活节奏，适应新的社会环境，同时也在努力保持和传承那些宝贵的传统和文化。这个国家的社会结构也在不断演变。随着教育水平的提高和社会意识的增强，人们对平等和公正的要求越来越高。政府在推动社会进步的同时，也在不断完善法律制度和社会保障体系。平等的机会、社会福利和人权保护，成为了这个国家发展的重要方向。人们的生活质量逐渐提高，社会的整体和谐也得到了改善。各种社会活动和公益事业的兴起，让人们在追求物质财富的同时，也更加关注社会责任和人际关系的和谐。科技的飞速发展对社会各个领域产生了深远的影响。互联网的普及、智能设备的广泛应用，改变了人们的沟通方式和生活习惯。信息技术的进步推动了各行各业的变革，从医疗、教育到金融、娱乐，每个领域都在经历着数字化和智能化的浪潮。电子商务的兴起让购物变得更加方便快捷，在线教育的普及让学习变得更加灵活多样。科技的发展不仅提高了生产效率，也丰富了人们的生活方式。在国际事务中，这个国家也发挥着重要作用。作为全球经济和政治的重要一员，它在国际组织和多边合作中积极参与，推动全球治理和国际合作。无论是应对气候变化、解决国际冲突，还是促进全球贸易和经济发展，这个国家都在为全球的和平与繁荣做出贡献。它与世界各国建立了广泛的外交关系，通过合作与交流，共同应对全球性挑战。这个国家的国际形象也因其在全球事务中的积极作用而得到了提升，赢得了国际社会的尊重和认可。文化交流也是这个国家对外开放的重要组成部分。通过文化交流活动，人民能够更加深入地了解其他国家的风俗习惯和文化背景，同时也向世界展示自己独特的文化魅力。各种文化交流项目、艺术展览和国际比赛，为不同国家和地区的人民提供了交流和学习的机会。通过这些活动，这个国家的文化影响力不断扩大，国际社会对其文化的认同度也在不断提高。人们通过艺术和文化的交流，不仅加深了对其他国家文化的理解，也促进了国际间的友谊和合作。教育的全球化也在不断推进。这个国家的教育体系不仅吸引了大量的国际学生，也在积极参与全球教育合作。国际化的教育项目和跨国交流项目，让学生们能够在多元文化的环境中成长。通过与其他国家的教育机构合作，分享教育资源和教学经验，推动教育领域的共同进步。教育的全球化不仅提升了国家的教育水平，也增强了国际间的文化理解和合作。未来，这个国家将继续在教育领域发挥重要作用，为全球教育的发展做出贡献。这个国家的科技创新不仅在国内产生了深远的影响，也在全球范围内引起了广泛关注。从传统的制造业到现代的高科技产业，这个国家一直致力于推动技术进步和创新。科技园区和研究机构的建立，为科技人才提供了良好的发展平台。政府的政策支持和投资推动了科技领域的快速发展。人工智能、大数据、区块链等前沿技术在这里得到了广泛应用，推动了各个行业的变革。无论是智能家居、自动驾驶还是医疗科技，这些创新技术都在不断提升人们的生活质量和生产效率。与此同时，这个国家也在注重科技伦理和社会责任。科技的进步带来了许多机遇，但也伴随着一些挑战。数据隐私、安全问题和技术滥用等问题，引发了社会各界的广泛关注。政府和科技企业正在积极探索制定相关法规和标准，确保科技的健康发展。在推动科技创新的同时，重视科技对社会的影响，推动科技与社会的和谐发展，成为了国家发展战略的重要组成部分。在环境保护方面，这个国家也采取了积极的措施。面对全球气候变化和环境污染的问题，国家制定了一系列环境保护政策。绿色能源、可再生资源的开发利用，减少碳排放和环境污染，成为了国家发展的重要目标。各种环保项目和绿色技术的应用，有效地改善了空气和水质，保护了生态环境。公众的环保意识也在不断提高，越来越多的人参与到环保行动中，共同推动可持续发展的实现。文化创意产业也是这个国家经济的重要组成部分。影视制作、音乐、文学等领域蓬勃发展，涌现出了一大批优秀的文化作品和艺术家。国家对文化创意产业的支持力度不断加大。真棒。
### 问题：请总结这篇文章。
### 回答：
"""

# tokens = tokenizer.encode(query_128)
# num_tokens = len(tokens)
# #print(num_tokens)

# tokens of query is 512
query = "In a world where technology has advanced beyond our wildest dreams, humanity stands on the brink of a new era. The year is 2050, and artificial intelligence has become an integral part of everyday life. Autonomous vehicles zip through the streets, drones deliver packages with pinpoint accuracy, and smart homes anticipate every need of their inhabitants. But with these advancements come new challenges and ethical dilemmas. As society grapples with the implications of AI, questions about privacy, security, and the nature of consciousness itself come to the forefront. Amidst this backdrop, a new breakthrough in quantum computing promises to revolutionize the field even further. Scientists have developed a quantum processor capable of performing calculations at speeds previously thought impossible. This leap in technology opens the door to solving problems that have long stumped researchers, from predicting climate change patterns with unprecedented accuracy to unraveling the mysteries of the human genome. However, the power of this new technology also raises concerns about its potential misuse. Governments and corporations race to secure their own quantum capabilities, sparking a new kind of arms race. Meanwhile, a group of rogue programmers, known as the Shadow Collective, seeks to exploit the technology for their own ends. As tensions rise, a young scientist named Dr. Evelyn Zhang finds herself at the center of this unfolding drama. She has discovered a way to harness quantum computing to create a true artificial general intelligence (AGI), a machine capable of independent thought and reasoning. Dr. Zhang's creation, named Athena, possesses the potential to either save humanity from its own worst impulses or to become the ultimate instrument of control. As she navigates the treacherous waters of corporate espionage, government intrigue, and ethical quandaries, Dr. Zhang must decide the fate of her creation and, with it, the future of humanity. Will Athena be a benevolent guardian or a malevolent dictator? The answer lies in the choices made by those who wield its power. The world watches with bated breath as the next chapter in the saga of human and machine unfolds. In the midst of these global tensions, everyday life continues. Children attend schools where AI tutors provide personalized learning experiences. Hospitals use advanced algorithms to diagnose and treat patients with greater accuracy than ever before. The entertainment industry is transformed by virtual reality experiences that are indistinguishable from real life."
my_query = "What is Deep Learning?"
query_rerank_1 = """Deep learning is a subset of machine learning, which itself is a branch of artificial intelligence (AI). It involves the use of neural networks with many layers—hence "deep." These networks are capable of learning from data in a way that mimics human cognition to some extent. The key idea is to create a system that can process inputs through multiple layers where each layer learns to transform its input data into a slightly more abstract and composite representation. In a typical deep learning model, the input layer receives the raw data, similar to the way our senses work. This data is then passed through multiple hidden layers, each of which transforms the incoming data using weights that are adjusted during training. These layers might be specialized to recognize certain types of features in the data, like edges or textures in an image, specific words or phrases in a text, or particular frequency patterns in audio. The final layer produces the output of the model, which could be a class label in classification tasks, a continuous value in regression, or a complex pattern in generative models. Deep learning has been behind many of the recent advancements in AI, including speech recognition, image recognition, natural language processing, and autonomous driving."""
query_rerank_2 = """Deep learning is a powerful tool in the field of artificial intelligence, but it's important to recognize what it is not. Deep learning is not a solution to all types of data processing or decision-making problems. While deep learning models excel at tasks involving large amounts of data and complex patterns, they are not as effective for tasks that require reasoning, logic, or understanding of abstract concepts, which are better handled by other types of AI algorithms. Deep learning is also not a synonym for all of machine learning. Traditional machine learning encompasses a broader range of techniques that include not only neural networks but also methods like decision trees, support vector machines, and linear regression. These traditional models often require less data and computational power and can be more interpretable than deep learning models. They are particularly useful in scenarios where the underlying relationships in the data are more straightforward or where transparency in decision-making is critical. Additionally, deep learning is not inherently unbiased or fair. The models can perpetuate or even amplify biases present in the training data, leading to unfair outcomes in applications like hiring, lending, and law enforcement."""

query_1k = """
### You are a helpful, respectful and honest assistant to help the user with questions. \
Please refer to the search results obtained from the local knowledge base. \
But be careful to not incorporate the information that you think is not relevant to the question. \
If you don't know the answer to a question, please don't share false information. \
### Search results: In a world where technology has advanced beyond our wildest dreams, humanity stands on the brink of a new era. The year is 2050, and artificial intelligence has become an integral part of everyday life. Autonomous vehicles zip through the streets, drones deliver packages with pinpoint accuracy, and smart homes anticipate every need of their inhabitants. But with these advancements come new challenges and ethical dilemmas. As society grapples with the implications of AI, questions about privacy, security, and the nature of consciousness itself come to the forefront. Amidst this backdrop, a new breakthrough in quantum computing promises to revolutionize the field even further. Scientists have developed a quantum processor capable of performing calculations at speeds previously thought impossible. This leap in technology opens the door to solving problems that have long stumped researchers, from predicting climate change patterns with unprecedented accuracy to unraveling the mysteries of the human genome. However, the power of this new technology also raises concerns about its potential misuse. Governments and corporations race to secure their own quantum capabilities, sparking a new kind of arms race. Meanwhile, a group of rogue programmers, known as the Shadow Collective, seeks to exploit the technology for their own ends. As tensions rise, a young scientist named Dr. Evelyn Zhang finds herself at the center of this unfolding drama. She has discovered a way to harness quantum computing to create a true artificial general intelligence (AGI), a machine capable of independent thought and reasoning. Dr. Zhang's creation, named Athena, possesses the potential to either save humanity from its own worst impulses or to become the ultimate instrument of control. As she navigates the treacherous waters of corporate espionage, government intrigue, and ethical quandaries, Dr. Zhang must decide the fate of her creation and, with it, the future of humanity. Will Athena be a benevolent guardian or a malevolent dictator? The answer lies in the choices made by those who wield its power. The world watches with bated breath as the next chapter in the saga of human and machine unfolds. In the midst of these global tensions, everyday life continues. Children attend schools where AI tutors provide personalized learning experiences. Hospitals use advanced algorithms to diagnose and treat patients with greater accuracy than ever before. The entertainment industry is transformed by virtual reality experiences that are indistinguishable from real life. Yet, for all the benefits, there are those who feel left behind by this technological revolution. Communities that once thrived on traditional industries find themselves struggling to adapt. The digital divide grows wider, creating new forms of inequality. Dr. Zhang's journey is not just a scientific quest but a deeply personal one. Her motivations are shaped by a desire to honor her late father's legacy, a pioneer in the field of AI who envisioned a future where technology would serve humanity's highest ideals. As she delves deeper into her research, she encounters allies and adversaries from unexpected quarters. A former colleague, Dr. Marcus Holt, now working for a rival tech giant, becomes both a rival and a potential ally as they navigate their complex relationship. In a hidden lab, far from prying eyes, Dr. Zhang and her team work tirelessly to refine Athena. They face numerous setbacks and breakthroughs, each step bringing them closer to their goal. The ethical implications of their work weigh heavily on them. Can a machine truly understand human emotions? Is it possible to program empathy and compassion? These questions haunt Dr. Zhang as she watches Athena's capabilities grow. As word of Athena's development leaks, the world reacts with a mixture of hope and fear. Protests erupt in major cities, with demonstrators demanding transparency and ethical oversight. Governments convene emergency sessions to discuss the potential impact of AGI on national security and global stability. Amid the chaos, the Shadow Collective launches a cyber-attack on Dr. Zhang's lab, attempting to steal her research. The attack is thwarted, but it serves as a stark reminder of the dangers they face. The final phase of Athena's development involves a series of tests to evaluate her decision-making abilities. This is the whole story.\n
### Question: Summarize the story above into three sentences.\n
### Answer:
"""

# tokens of query is 1k
query_llm = "In a world where technology has advanced beyond our wildest dreams, humanity stands on the brink of a new era. The year is 2050, and artificial intelligence has become an integral part of everyday life. Autonomous vehicles zip through the streets, drones deliver packages with pinpoint accuracy, and smart homes anticipate every need of their inhabitants. But with these advancements come new challenges and ethical dilemmas. As society grapples with the implications of AI, questions about privacy, security, and the nature of consciousness itself come to the forefront. Amidst this backdrop, a new breakthrough in quantum computing promises to revolutionize the field even further. Scientists have developed a quantum processor capable of performing calculations at speeds previously thought impossible. This leap in technology opens the door to solving problems that have long stumped researchers, from predicting climate change patterns with unprecedented accuracy to unraveling the mysteries of the human genome. However, the power of this new technology also raises concerns about its potential misuse. Governments and corporations race to secure their own quantum capabilities, sparking a new kind of arms race. Meanwhile, a group of rogue programmers, known as the Shadow Collective, seeks to exploit the technology for their own ends. As tensions rise, a young scientist named Dr. Evelyn Zhang finds herself at the center of this unfolding drama. She has discovered a way to harness quantum computing to create a true artificial general intelligence (AGI), a machine capable of independent thought and reasoning. Dr. Zhang's creation, named Athena, possesses the potential to either save humanity from its own worst impulses or to become the ultimate instrument of control. As she navigates the treacherous waters of corporate espionage, government intrigue, and ethical quandaries, Dr. Zhang must decide the fate of her creation and, with it, the future of humanity. Will Athena be a benevolent guardian or a malevolent dictator? The answer lies in the choices made by those who wield its power. The world watches with bated breath as the next chapter in the saga of human and machine unfolds. In the midst of these global tensions, everyday life continues. Children attend schools where AI tutors provide personalized learning experiences. Hospitals use advanced algorithms to diagnose and treat patients with greater accuracy than ever before. The entertainment industry is transformed by virtual reality experiences that are indistinguishable from real life. Yet, for all the benefits, there are those who feel left behind by this technological revolution. Communities that once thrived on traditional industries find themselves struggling to adapt. The digital divide grows wider, creating new forms of inequality. Dr. Zhang's journey is not just a scientific quest but a deeply personal one. Her motivations are shaped by a desire to honor her late father's legacy, a pioneer in the field of AI who envisioned a future where technology would serve humanity's highest ideals. As she delves deeper into her research, she encounters allies and adversaries from unexpected quarters. A former colleague, Dr. Marcus Holt, now working for a rival tech giant, becomes both a rival and a potential ally as they navigate their complex relationship. In a hidden lab, far from prying eyes, Dr. Zhang and her team work tirelessly to refine Athena. They face numerous setbacks and breakthroughs, each step bringing them closer to their goal. The ethical implications of their work weigh heavily on them. Can a machine truly understand human emotions? Is it possible to program empathy and compassion? These questions haunt Dr. Zhang as she watches Athena's capabilities grow. As word of Athena's development leaks, the world reacts with a mixture of hope and fear. Protests erupt in major cities, with demonstrators demanding transparency and ethical oversight. Governments convene emergency sessions to discuss the potential impact of AGI on national security and global stability. Amid the chaos, the Shadow Collective launches a cyber-attack on Dr. Zhang's lab, attempting to steal her research. The attack is thwarted, but it serves as a stark reminder of the dangers they face. The final phase of Athena's development involves a series of tests to evaluate her decision-making abilities. Dr. Zhang designs scenarios that challenge Athena to balance competing interests and make ethical choices. In one test, Athena must decide whether to divert a runaway trolley to save a group of people at the expense of one individual. In another, she is tasked with allocating limited medical resources during a pandemic. Each test pushes the boundaries of machine ethics and highlights the complexities of programming morality. Summarize the story above."
# length of my_embedding is 768
my_embedding = [
    0.00030903306, -0.06356524, 0.0025720573, -0.012404448, 0.050649878, 0.023426073, 0.022131812, 0.000759529,
    -0.00021144224, -0.03351229, -0.024963351, 0.0064628883, -0.007054883, 0.066674456, 0.0013026494, 0.046839874,
    0.06272031, -0.021033816, 0.011214508, 0.043999936, -0.050784662, -0.06221004, -0.04018244, 0.017779319,
    -0.0013301502, 0.0022156204, -0.043744676, 0.012752031, -0.023972677, 0.011199989, 0.028703978, -0.0089899,
    0.03712499, -0.027488017, 0.016138831, 0.041751742, -0.03958115, -0.03528769, -0.022453403, -0.019844962,
    -0.018594252, -0.042406067, -0.0120475935, 0.049004447, -0.08094748, 0.017947419, -0.12090019, 0.0023762283,
    -0.022721844, -0.0122670885, -0.07537693, 0.051195897, 0.032084838, -0.0191422, 0.042885557, 0.0152152525,
    0.0042946604, -0.08067345, 0.010296512, -0.05629215, 0.051881734, 0.037080515, -0.018511552, -0.027629064,
    -0.0010543121, -0.02618493, 0.024228664, 0.042858265, -0.02330382, -0.0034123377, -0.028686361, 0.029237133,
    -0.020652898, -0.005005634, -0.052511718, -0.011031183, 0.012807135, 0.0143450685, 0.08218706, -0.008386834,
    0.0036734014, 0.06236072, 0.04255367, 0.03158083, 0.004631116, 0.0007993413, -0.019410692, -0.004640353,
    -0.044894144, 0.022581149, 0.010380893, -0.053084206, 0.060135297, 0.051447738, 0.014172936, 0.0076013976,
    0.01375325, -0.035371594, -0.011681993, -0.014776056, -0.023268431, -0.0590664, -0.016947128, -0.0146322865,
    -0.048343826, 0.026675656, 0.052418776, -0.013986488, 0.014608619, -0.019658033, -0.0014043319, -0.008499042,
    -0.0025460746, -0.04858996, -0.04293979, -0.00791175, -0.01644228, 0.0038053868, -0.025010196, -0.04599194,
    0.03430527, 0.0382939, 0.0019500003, 0.021234535, -0.03411336, 0.015422987, 0.0040041124, 0.018236278,
    0.004566607, -0.02694257, 0.020603696, 0.0168677, -0.007864176, 0.02186715, -0.014774427, 0.00078197615,
    -0.020355146, 0.006654448, 0.025772778, 0.009957317, -0.0025282202, -0.0579994, 0.030099394, -0.03549671,
    0.05439607, -0.015254235, -0.007988717, -0.004305188, -0.018912116, 0.0027841094, -0.044504374, 0.05556499,
    -0.018894102, -0.049442377, 0.008305442, 0.039805025, -0.00042916916, 0.0059957127, 0.034555893, 0.02306613,
    0.05890197, -0.019604865, -0.05472663, -0.009928875, -0.02455136, -0.054289207, 0.055403363, 0.024503028,
    -0.019979116, 0.025056925, -0.0020133695, -0.011331945, 0.020181546, -0.012020893, 0.011718686, 0.047295712,
    0.028600235, 0.034037635, 0.043115, 0.051445063, -0.065478735, 0.046462707, -0.00893844, -0.0063705654,
    -0.044797033, -0.03157799, 0.04950285, -0.010792562, 0.03688506, 0.014347515, -0.063743494, -0.036214367,
    -0.03380074, -0.03769261, 0.033050846, -0.016999796, -0.015086913, 0.082186624, -0.011051229, 0.04645044,
    0.054343436, -0.05152064, 0.015258479, -0.016340451, -0.027205588, 0.029828794, 0.01575663, -0.04375617,
    -0.003217223, 0.0033928305, 0.0076283724, -0.049442016, -0.0053870296, 0.001464261, 0.043246116, 0.030448606,
    -0.007991404, -0.00472732, 0.0065691406, -0.018045014, 0.0050486918, -0.042211313, 0.024785575, 0.002973673,
    0.008309046, 0.08794761, 0.041150656, -0.051644977, 0.03518446, -0.037274398, 0.003677234, 0.02468397,
    -0.012616027, 0.019353414, 0.013835055, -0.027715908, 0.014544011, 0.0104869455, 0.04520827, -0.03349062,
    -0.070577316, 0.006990252, -0.047459435, 0.05270745, 0.011758987, 0.009585331, 0.033369783, -0.014058916,
    -0.01459581, -0.016755696, -0.004542376, 0.00010269242, 0.016674489, 0.029076884, -0.02398147, -0.059065636,
    0.0021090624, -0.009751267, 0.10289938, 0.027459696, -0.050843943, 0.051473383, -0.027577678, 0.022293199,
    -0.02546725, -0.095162235, -0.02834687, -0.020029712, 0.08765645, -0.014138398, 0.048151582, 0.0074673486,
    0.03930912, 8.716728e-05, -0.026958048, 0.0055812267, 0.054877758, 0.055222698, -0.012584492, -0.04345845,
    -0.02426138, 0.066533394, 0.0056506116, -0.015095139, 0.027254738, -0.025936818, -0.0030386604, -0.008605405,
    -0.00891901, 0.0043280497, 0.03594552, 0.061649352, -0.042369556, 0.048818704, 0.021097481, 0.053623416,
    0.045890126, -0.02760507, -0.01573271, 8.311729e-05, -0.007044427, 0.039558847, -0.021737648, 0.03881644,
    0.020095227, -0.0130994925, 0.07956597, -0.014619613, -0.196594, -0.012995427, 0.017993039, -0.0073582316,
    0.03813464, -0.05930209, -0.005811095, -0.009954021, 0.0018040026, -0.02305836, -0.027102914, -0.006594491,
    0.03801163, 0.025225805, 0.019853814, -0.01661875, 0.00875584, -0.016539048, -0.036775734, 0.045325384,
    -0.031573802, -0.029247303, -0.01253526, 0.07143945, -0.029145112, 0.027142324, -0.084799446, -0.05071047,
    -0.0028705404, -0.0021605634, -0.023848932, -0.028478833, -0.0324437, 0.04862323, 0.023280755, 0.016372373,
    0.027676713, -0.03990074, -0.002498963, 0.017739112, -0.03355715, -0.048603803, 0.003019928, -0.040887985,
    0.044802677, 0.015728928, -0.09309996, -0.04836613, -0.014831327, 0.0010454153, -0.010638626, -0.024611702,
    -0.06786172, -0.0013613648, 0.015592544, -0.004870558, 0.0025347366, -0.012121049, -0.024824884, 0.036656864,
    -0.0031881756, -0.020234713, -0.02279762, -0.05922489, -0.020922685, -0.02317517, -0.0610787, -0.062339265,
    0.017110312, 0.03338325, -0.010112536, 0.048114073, -0.06444785, -0.04852081, 0.006865087, -0.025729232,
    -0.029516479, -0.00941828, 0.05484419, 0.027107889, 0.008253239, -0.06284466, 0.035466067, 0.012162117,
    -0.009598869, -0.048561577, 0.046412956, -0.03714821, -0.020295296, -0.028690876, 0.06459795, -0.006428147,
    -0.026629865, -0.026355268, 0.03504117, 0.019873064, 0.0032821875, 0.028802538, -0.013105742, 0.019568242,
    -0.021279998, -0.024270158, -0.04382199, -0.016565602, -0.040926415, -0.022030178, -0.009905917, 0.030040652,
    0.10125908, -0.00263213, -0.037816163, 0.014336923, 0.025456406, 0.00100471, 0.00032630135, -0.030703938,
    0.016242733, 0.0013898151, 0.018662402, -0.038746417, -0.03208466, 0.05599271, 0.0056110374, 0.04541296,
    0.015634691, -0.0295602, 0.0008552127, 0.0152370455, 0.01917365, -0.025870943, 0.020953277, -0.0003668304,
    0.012462414, 0.008920647, -0.0016022202, -0.012868524, -0.010962337, -0.0068797423, -0.009876324, 0.009545094,
    -0.0076226145, 0.0016608062, 0.01671912, -0.015954005, -0.020932103, 0.049466487, -0.073524654, 0.060834516,
    -0.0069076903, -0.014720568, 0.014687667, -0.028758403, 0.025296489, -0.058295064, 0.0300228, -0.0070548407,
    0.010030844, -0.0065278015, -0.028693652, -0.04413148, 0.010020056, 0.03030962, -0.009985439, 0.0104528945,
    0.055963244, 0.054369748, -0.026280807, -0.061695196, 0.03131826, 0.012127447, 0.034067005, -0.029661555,
    -0.008471412, -0.031715434, -0.014869134, 0.036652327, 0.026443308, -0.005586143, 0.02489041, 0.058810584,
    0.017560603, 0.039287437, -0.0034399417, 0.033162847, 0.050130997, 0.032992795, -0.029766096, 0.0061241565,
    -0.055100117, 0.028030321, -0.038325004, 0.024334624, -0.017313298, -0.019499615, -0.01981792, -0.027658446,
    -0.018781614, 0.047175173, -0.0034721645, -0.020667735, -0.039781824, -0.019210767, -0.026337992, -0.023234084,
    0.04964025, -0.07777429, 0.030660955, 0.048808888, 0.044913623, 0.03674177, -0.011647912, -0.02756851,
    -0.07255596, -0.087645784, -0.039343175, -0.04203861, -0.0039666323, 0.01671798, 0.026770905, -0.03026136,
    0.029986707, 0.024289394, 0.0117887445, -0.012229226, -0.047474023, -0.03667933, 0.026632814, 0.03635988,
    0.0005169153, 0.017991144, 0.009195582, -0.0069137816, 0.011830262, -0.005349248, -0.034725383, 0.031615537,
    -0.05287625, 0.014696611, -0.014054976, -0.016312832, 0.0019933872, 0.02526325, -0.07060638, 0.010108201,
    -0.014116627, -0.0059261527, -0.008993763, 0.021177163, -0.04376879, -0.028056782, 0.06090816, 0.0039020707,
    -0.038584042, -0.048930347, 0.023969071, -0.059767634, -0.029087082, -0.055471163, -0.0693663, -0.005782939,
    -0.02213406, -0.008931021, -0.0056467317, 0.029872, 0.022359788, 0.008790491, -0.03974519, -0.0064023994,
    0.065675184, -0.01572894, -0.03746496, -0.061758112, -0.028639734, 0.08637485, 0.031286176, -0.0007831992,
    0.0030584438, 0.012293266, 0.020008529, -0.028351337, 0.0020157974, 0.027084284, 0.0027892909, -0.03614263,
    0.006040403, -0.0475395, -0.004725341, -0.021484248, -0.022895435, -0.015276968, -0.04321307, -0.04412736,
    -0.005665974, -0.009453732, -0.028690176, 0.010030023, 0.027899086, 0.060336158, 0.06936418, 0.006905735,
    -0.024200331, 0.04907079, 0.0031401473, 0.00441764, -0.029459601, 0.03803177, -0.0353827, -0.04895069,
    0.04761868, 0.007312183, -0.008343287, -0.035251893, 0.036832787, 0.0246635, -0.03892744, 0.018956844,
    0.013805393, -0.048437007, -0.04829463, 0.022492649, -0.029296776, 0.041375805, 0.046585515, 0.020296978,
    0.03789685, 0.059837162, 0.011104047, -0.032134652, 0.07064702, 0.04802412, 0.01730015, 0.07398111,
    -0.049616653, 0.073309965, -0.009425022, -0.06281925, 0.024277369, 0.021769999, 0.018801004, 0.020460334,
    -0.017282128, 0.02107381, 0.050663974, 0.05384202, -0.015786275, 0.054115638, 0.051110543, 0.07228662,
    -0.0297164, 0.048188735, 0.0064821052, -0.025109168, 0.013359567, -0.021189261, 0.025518114, -0.048609257,
    0.035189547, 0.08076792, 0.0037926896, -0.015581124, 0.0021879557, 0.03258444, 0.1159761, -0.021879155,
    -0.029991308, 0.016155615, -0.0064807986, -0.06050641, -0.0056326366, 0.028292047, -0.02181108, 0.032760337,
    -0.02199964, -0.034708463, 0.011786828, -0.035356887, -0.014913256, -0.039785992, -0.021320345, 0.026806,
    -0.002236271, 0.044643793, -0.015494709, -0.0065790443, 0.0066197272, -0.0050217584, -0.077643394, 0.054302536,
    0.02795664, -0.03983502, -0.027030395, -0.024944995, -0.0022802327, 0.07870793, -0.034157082, 0.037108578,
    0.044204045, 0.012753803, 0.0037155224, 0.008254912, 0.013719737, -0.010619027, -0.021691227, 0.05794269,
    -0.075987175, -0.054171626, 0.0038932571, 0.0039806664, -0.037909392, -0.030339854, 0.063346766, -0.088324875,
    -0.06095589, 0.08515697, 0.020457987, 0.080888115, 0.032549396, 0.003924944, 0.029362155, 0.012281526,
    -0.06369542, 0.023577815, -0.017478395, -0.0016188929, 0.01734596, 0.043068424, 0.049590185, 0.028447397,
    0.021328118, -0.0025053236, -0.030895222, -0.055287424, -0.045610603, 0.04216762, -0.027732681, -0.036629654,
    0.028555475, 0.066825, -0.061748896, -0.08889239, 0.045914087, -0.004745301, 0.034891862, -0.0065364013,
    -0.0069724764, -0.061335582, 0.02129905, -0.02776986, -0.0246678, 0.03999176, 0.037477136, -0.006806653,
    0.02261455, -0.04570737, -0.033122733, 0.022785513, 0.0160026, -0.021343587, -0.029969815, -0.0049176104
]

DATAS = {
    "tei_embedding": {
        "inputs": query_128
    },
    "mosec_embedding": {
        "input": query_128,
        "model": "/root/bge-large-zh-v1.5"
    },
    "embedding": {
        "text": query_128
    },
    "neuralspeed_embedding": {
        "query": query_128
    },
    "guardrail": {
        "text": "How do you buy a tiger in the US?"
    },
    "retrieval": {
        "text": my_query,
        "embedding": my_embedding
    },
    "tei_rerank": {
        "query": my_query,
        "texts": [query_rerank_1, query_rerank_2]
    },
    "mosec_rerank": {
        "query": my_query,
        "texts": [query_rerank_1, query_rerank_2]
    },
    "reranking": {
        "initial_query": my_query,
        "retrieved_docs": [{
            "text": query_rerank_1
        }, {
            "text": query_rerank_2
        }]
    },
    "tgi": {
        "inputs": query_llm,
        "parameters": {
            "max_new_tokens": 128
        }
    },
    "llm": {
        "query": query_llm,
        "max_new_tokens": 128
    },
    "rag": {
        "messages": query_128,
        "max_tokens": 128
    },
}


def send_single_request(task, idx, queries, concurrency, url):
    res = []
    headers = {"Content-Type": "application/json"}
    data = DATAS[task]
    while idx < len(queries):
        start_time = time.time()
        response = requests.post(url, json=data, headers=headers)
        end_time = time.time()
        res.append({"idx": idx, "start": start_time, "end": end_time})
        idx += concurrency
        print(response.content)
    return res


def send_concurrency_requests(task, request_url, num_queries):
    if num_queries <= 5:
        concurrency = 1
    else:
        concurrency = num_queries // 5
    responses = []
    stock_queries = [query for _ in range(num_queries)]
    test_start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = []
        for i in range(concurrency):
            futures.append(
                executor.submit(send_single_request,
                                task=task,
                                idx=i,
                                queries=stock_queries,
                                concurrency=concurrency,
                                url=request_url))
        for future in concurrent.futures.as_completed(futures):
            responses = responses + future.result()
    test_end_time = time.time()

    print("=======================")
    for r in responses:
        r["total_time"] = r["end"] - r["start"]
        print("query:", r["idx"], "    time taken:", r["total_time"])

    print("=======================")
    print(f"Total Concurrency: {concurrency}")
    print(f"Total Requests: {len(stock_queries)}")
    print(f"Total Test time: {test_end_time - test_start_time}")

    response_times = [r["total_time"] for r in responses]

    # Calculate the P50 (median)
    p50 = numpy.percentile(response_times, 50)
    print("P50 total latency is ", p50, "s")

    # Calculate the P99
    p99 = numpy.percentile(response_times, 99)
    print("P99 total latency is ", p99, "s")

    return p50, p99


def send_single_request_zh(task, idx, queries, concurrency, url, data_zh=None):
    res = []
    headers = {"Content-Type": "application/json"}
    query = random.choice(data_zh)
    data = {"messages": query, "max_tokens": 128}
    if task == "rag":
        data = {"messages": query, "max_tokens": 128}
    elif task == "embedding":
        data = {"text": query}
    elif task == "llm":
        data = {"query": query, "max_new_tokens": 128}
    print(data)
    while idx < len(queries):
        start_time = time.time()
        response = requests.post(url, json=data, headers=headers)
        end_time = time.time()
        res.append({"idx": idx, "start": start_time, "end": end_time})
        idx += concurrency
        print(response.content)
    return res


def send_single_request_v2(task, idx, queries, concurrency, url, data_zh=None):
    res = []
    headers = {"Content-Type": "application/json"}
    data = DATAS[task]
    if task == "neuralspeed_embedding":
        data = msgspec.msgpack.encode(data)
    print(data)
    while idx < len(queries):
        start_time = time.time()
        if task in ["llm", "tgi", "rag"]:
            start_time = time.time()
            response = requests.post(url, json=data, headers=headers, stream=True)
            idx += concurrency
            token_idx = 0
            is_first = True
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    if is_first:
                        first_token_finished_time = time.time()
                        is_first = False

                    token_idx += 1
                    #print("chunk: ", chunk)
            end_time = time.time()  # end time equals to the last_token_finished_time
            res.append({
                "idx": idx,
                "start": start_time,
                "end": end_time,
                "first_token_finished_time": first_token_finished_time,
                "token_num": token_idx - 1
            })
            #print("token_num===", token_idx-1)
        else:
            start_time = time.time()
            if task == "neuralspeed_embedding":
                response = requests.post(url, data=data, headers=headers)
            else:
                response = requests.post(url, json=data, headers=headers)
            #response = requests.post(url, data=msgspec.msgpack.encode(data), headers=headers)
            end_time = time.time()
            res.append({"idx": idx, "start": start_time, "end": end_time})
            idx += concurrency
            print(response.content)
    return res


def send_concurrency_requests_v2(task, request_url, num_queries):
    if num_queries <= 5:
        concurrency = 1
    else:
        concurrency = num_queries // 5

    responses = []
    stock_queries = [query for _ in range(num_queries)]
    test_start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = []
        for i in range(concurrency):
            futures.append(
                executor.submit(
                    send_single_request_v2,
                    task=task,
                    idx=i,
                    queries=stock_queries,
                    concurrency=concurrency,
                    url=request_url,
                ))
        for future in concurrent.futures.as_completed(futures):
            responses = responses + future.result()
    test_end_time = time.time()

    print("=======================")
    if task in ["llm", "tgi", "rag"]:
        for r in responses:
            r["total_time"] = r["end"] - r["start"]
            r["first_token_time"] = r["first_token_finished_time"] - r["start"]
            r["avg_token_time"] = (r["end"] - r["first_token_finished_time"]) / r["token_num"]
            print("query:", r["idx"], "    time taken:", r["total_time"], "     first token latency:",
                  r["first_token_time"], "     average token latency", r["avg_token_time"], "     token_chunk:",
                  r["token_num"])
    else:
        for r in responses:
            r["total_time"] = r["end"] - r["start"]
            print("query:", r["idx"], "    time taken:", r["total_time"])

    print("=======================")
    print(f"Total Concurrency: {concurrency}")
    print(f"Total Requests: {len(stock_queries)}")
    print(f"Total Test time: {test_end_time - test_start_time}")

    response_times = [r["total_time"] for r in responses]
    print("responses===================", responses)
    if task in ["llm", "tgi", "rag"]:
        first_token_times = [r["first_token_time"] for r in responses]
        avg_token_time = [r["avg_token_time"] for r in responses]

    # Calculate the P50 (median)
    p50_total = numpy.percentile(response_times, 50)
    avg_total = numpy.mean(response_times)
    print("P50 total latency is ", p50_total, "s")
    if task in ["llm", "tgi", "rag"]:
        p50_first = numpy.percentile(first_token_times, 50)
        p50_avg = numpy.percentile(avg_token_time, 50)
        print("P50 first token latency is ", p50_first, "s")
        print("P50 average token latency is ", p50_avg, "s")

    p90_total = numpy.percentile(response_times, 90)
    print("P90 total latency is ", p90_total, "s")
    if task in ["llm", "tgi", "rag"]:
        p90_first = numpy.percentile(first_token_times, 90)
        p90_avg = numpy.percentile(avg_token_time, 90)
        print("P90 first token latency is ", p90_first, "s")
        print("P90 average token latency is ", p90_avg, "s")

    # Calculate the P99
    p99_total = numpy.percentile(response_times, 99)
    print("P99 total latency is ", p99_total, "s")
    if task in ["llm", "tgi", "rag"]:
        p99_first = numpy.percentile(first_token_times, 99)
        p99_avg = numpy.percentile(avg_token_time, 99)
        print("P99 first token latency is ", p99_first, "s")
        print("P99 average token latency is ", p99_avg, "s")

    if task in ["llm", "tgi", "rag"]:
        return avg_total, p50_total, p90_total, p99_total, p50_first, p90_first, p99_first, p50_avg, p90_avg, p99_avg
    else:
        return avg_total, p50_total, p90_total, p99_total


def send_concurrency_requests_zh(task, request_url, num_queries):
    if num_queries <= 4:
        concurrency = 1
    else:
        concurrency = num_queries // 4

    data_zh = []
    file_path = './stress_benchmark/data_zh.txt'
    with open(file_path, 'r') as file:
        for line in file:
            data_zh.append(line.strip())

    responses = []
    stock_queries = [query for _ in range(num_queries)]
    test_start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = []
        for i in range(concurrency):
            futures.append(
                executor.submit(send_single_request_zh,
                                task=task,
                                idx=i,
                                queries=stock_queries,
                                concurrency=concurrency,
                                url=request_url,
                                data_zh=data_zh))
        for future in concurrent.futures.as_completed(futures):
            responses = responses + future.result()
    test_end_time = time.time()

    print("=======================")
    for r in responses:
        r["total_time"] = r["end"] - r["start"]
        print("query:", r["idx"], "    time taken:", r["total_time"])

    print("=======================")
    print(f"Total Concurrency: {concurrency}")
    print(f"Total Requests: {len(stock_queries)}")
    print(f"Total Test time: {test_end_time - test_start_time}")

    response_times = [r["total_time"] for r in responses]

    # Calculate the P50 (median)
    p50 = numpy.percentile(response_times, 50)
    print("P50 total latency is ", p50, "s")

    # Calculate the P99
    p99 = numpy.percentile(response_times, 99)
    print("P99 total latency is ", p99, "s")

    return p50, p99


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Concurrent client to send POST requests")
    parser.add_argument("--task", type=str, default="llm", help="Task to perform")
    parser.add_argument("--url", type=str, default="http://localhost:8080", help="Service URL")
    parser.add_argument("--num-queries", type=int, default=192, help="Number of queries to be sent")
    parser.add_argument("--zh", help="data_zh", action="store_true")
    args = parser.parse_args()

    if args.zh:
        send_concurrency_requests_zh(args.task, args.url, args.num_queries)
    else:
        send_concurrency_requests(args.task, args.url, args.num_queries)
