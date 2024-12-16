# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import datetime
import json
import os

import requests
from tqdm import tqdm

from evals.metrics import bleu_score, rougeL_score
from evals.metrics.answer_relevancy import AnswerRelevancyMetric


class Evaluator:
    def __init__(
        self, dataset: list[dict] = None, output_path: str = None, task: str = None, llm_endpoint: str = None
    ) -> None:
        """Args:
        dataset (list[dict]): The dataset for evaluation.
        output_path (str): The path to save results.
        task (str): Task to evaluate.
        """
        self.task = task
        self.output_path = output_path
        self.dataset = dataset
        if llm_endpoint is None:
            self.llm_judge = None
        else:
            self.llm_judge = AnswerRelevancyMetric(model=llm_endpoint)

    @staticmethod
    def ingest_docs(documents_path: str, database_endpoint: str, chunk_size: int, chunk_overlap: int):
        """Args:
        documents_path (str): The path to documents.
        database_endpoint (str): URL of database.
        """
        files = []
        if os.path.isfile(documents_path):
            files.append(documents_path)
        elif os.path.isdir(documents_path):
            for root, dirs, files_ in os.walk(documents_path):
                files += [os.path.join(root, f) for f in files_]
        for file in tqdm(files):
            file_obj = open(file, mode="rb")
            response = requests.post(
                database_endpoint,
                files={"files": file_obj},
                data={"chunk_size": chunk_size, "chunk_overlap": chunk_overlap},
            )
            if response.ok:
                print(f"Successfully ingested {file}.")
            else:
                print(f"Failed to ingest {file}.")
            file_obj.close()

    def get_ground_truth_text(self, data: dict):
        raise NotImplementedError("Depends on the specific dataset.")

    def get_query(self, data: dict):
        raise NotImplementedError("Depends on the specific dataset.")

    def get_document(self, data: dict):
        raise NotImplementedError("Depends on the specific dataset.")

    def scoring(self, data: dict) -> dict:
        generated_text = data["generated_text"]
        ground_truth_text = self.get_ground_truth_text(data)
        data["ground_truth_text"] = ground_truth_text

        bleu_avg, bleu1, bleu2, bleu3, bleu4 = bleu_score(generated_text, ground_truth_text)
        if self.llm_judge is None:
            llm_score = 0.0
        else:
            llm_score = self.llm_judge.measure_zh(
                {"input": ground_truth_text, "actual_output": generated_text, "template": "zh"}
            )

        return {
            "metrics": {
                "bleu-avg": bleu_avg or 0.0,
                "bleu-1": bleu1 or 0.0,
                "bleu-2": bleu2 or 0.0,
                "bleu-3": bleu3 or 0.0,
                "bleu-4": bleu4 or 0.0,
                "rouge-L": rougeL_score(generated_text, ground_truth_text) or 0.0,
                "LLM-score": llm_score or 0.0,
                "length": len(generated_text),
            },
            "log": {
                "generated_text": generated_text,
                "ground_truth_text": ground_truth_text,
                "evaluateDatetime": str(datetime.datetime.now()),
            },
            "valid": len(generated_text.strip()) != 0,
        }

    def compute_overall(self, results: list[dict]) -> dict:
        overall = {
            "bleu-avg": 0,
            "bleu-1": 0,
            "bleu-2": 0,
            "bleu-3": 0,
            "bleu-4": 0,
            "rouge-L": 0,
            "LLM-score": 0.0,
            "length": 0,
        }

        for result in results:
            overall = {key: overall[key] + result["metrics"][key] for key in overall.keys()}

        overall_save = {f"avg. {key}": value / len(results) for key, value in overall.items()}

        overall_save["num"] = len(results)

        return overall_save

    def save_output(self, output: dict) -> None:
        """Save evaluation results."""
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=4)

    def read_output(self) -> dict:
        with open(self.output_path) as f:
            return json.load(f)

    def remove_invalid(self, results: list[dict]) -> list[dict]:
        """Remove invalid results from the list and return the cleaned results."""
        return [result for result in results if result["valid"]]

    def get_template(self):
        raise NotImplementedError("Depends on the specific dataset.")

    def extract_chunk_str(self, chunk_str):
        if chunk_str == "data: [DONE]\n\n":
            return ""
        prefix = "data: "
        prefix_2 = 'data: '
        suffix = "\n\n"
        suffix_2 = '\n\n'
        if chunk_str.startswith(prefix) or chunk_str.startswith(prefix_2):
            chunk_str = chunk_str[len(prefix) :]
        # print(chunk_str)
        if chunk_str.endswith(suffix) or chunk_str.endswith(suffix_2):
            chunk_str = chunk_str[: -len(suffix)]
        # print(chunk_str)
        chunk_str = eval(chunk_str)
        # print(chunk_str)
        # print(type(chunk_str))
        chunk_str = chunk_str.decode("utf-8")
        # print(chunk_str)
        # exit()
        return chunk_str

    def send_request(self, data, arguments):
        service_url = arguments.service_url
        headers = {"Content-Type": "application/json"}
        json_data = {}
        query = self.get_query(data)
        json_data["messages"] = query
        json_data["stream"] = True
        json_data["top_n"] = 2
        #json_data["temperature"] = arguments.temperature
        json_data["temperature"] = 0
        print("arguments.temperature", json_data['temperature'])
        json_data["max_new_tokens"] = arguments.max_new_tokens
        print("arguments.max_new_tokens", json_data['max_new_tokens'])
        json_data["chat_template"] = self.get_template()
        json_data = json.dumps(json_data)
        # print("==*"*20)
        # print('json_data=', json_data)
        chat_response = ""
        with requests.post(service_url, data=json_data, headers=headers, stream=True) as response:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    chunk = chunk.decode("utf-8")
                    print("chunk = ", chunk)
                    chat_response += self.extract_chunk_str(chunk)
                # print(chunk.decode("utf-8"), end="", flush=True)  # Flush to ensure immediate output

        print("chat response = ", chat_response)
        return chat_response
        # response = requests.post(service_url, data=json_data, headers=headers)
        #print("==*"*20)
        #print(response)
        #print(response.text)
        #exit()
        # print(response.json())
        """
        if response.ok:
            return self.post_process(response.json()["choices"][0]["message"]["content"])
        else:
            print(f"Request for pipeline failed due to {response.text}.")
            return ""
        """

    def post_process(self, result):
        return result

    def get_retrieved_documents(self, data, arguments):
        query = self.get_query(data)
        data = {"inputs": query}
        headers = {"Content-Type": "application/json"}
        response = requests.post(arguments.tei_embedding_endpoint + "/embed", data=json.dumps(data), headers=headers)
        if response.ok:
            embedding = response.json()[0]
        else:
            print(f"Request for embedding failed due to {response.text}.")
            return []
        data = {
            "text": query,
            "embedding": embedding,
            "search_typ": "similarity",
            "k": 4,
            "fetch_k": 20,
            "lambda_mult": 0.5,
        }
        response = requests.post(arguments.retrieval_endpoint, data=json.dumps(data), headers=headers)
        if response.ok:
            retrieved_documents = response.json()["retrieved_docs"]
            return [doc["text"] for doc in retrieved_documents]
        else:
            print(f"Request for retrieval failed due to {response.text}.")
            return []

    def scoring_retrieval(self, data, retrieved_documents):
        ground_truth_documents = self.get_document(data)

    def evaluate(self, arguments, sort=True, show_progress_bar=False, contain_original_data=False):
        """Run a complete evaluation.

        Args:
            arguments: Arguments.
            sort (bool): Whether to sort the results by id.
            show_progress_bar (bool): Whether to display a progress bar.
            contain_original_data (bool): Whether to include original data in the results for debugging.

        Returns:
            dict: Output dictionary contains fields such as: overall, results, etc.
        """
        if os.path.exists(self.output_path):  # Resume evaluation
            results = self.read_output().get("results", [])
            results = self.remove_invalid(results)
            saved_ids = [result["id"] for result in results]
        else:
            results = []
            saved_ids = []

        for data in tqdm(self.dataset) if show_progress_bar else self.dataset:
            if data["ID"] in saved_ids:
                continue  # Skip results that have already been evaluated and are valid
            try:
                retrieved_documents = self.get_retrieved_documents(data, arguments)
                data["retrieved_documents"] = retrieved_documents
                #generated_text = self.send_request(data, arguments)
                #generated_text="response> 《关于恢复和扩大消费措施》中提到的优化汽车购买使用管理的具体政策包括：\n\n1. 各地区不得新增汽车限购措施，已实施限购的地区需要因地制宜优化汽车限购措施。\n2. 着力推动全面取消二手车限迁政策，便利二手车交易登记，确保已出台的政策落地见效。\n3. 鼓励汽车更新消费，支持以旧换新，促进汽车市场的活跃度和消费潜力的释放。"

                #generated_text="国务院办公厅转发国家发展改革委《关于恢复和扩大消费的措施》中，关于汽车购买使用管理的措施包括以下几点：\n\n1. **优化汽车限购措施**：各地区不得新增汽车限购措施，对于已经实施限购的地区，应根据实际情况优化限购措施。\n\n2. **促进新能源汽车消费**：落实构建高质量充电基础设施体系、支持新能源汽车下乡、延续和优化新能源汽车车辆购置税减免等政策，以促进新能源汽车的消费。\n\n3. **全面取消二手车限迁**：推动全面取消二手车限迁政策的落地，便利二手车交易登记。\n\n4. **鼓励汽车更新消费**：鼓励以旧换新，通过政策激励促进汽车更新消费。\n\n这些措施旨在通过优化汽车购买和使用环境，促进汽车消费，特别是新能源汽车和二手车市场的健康发展，从而对整体消费市场产生积极影响。"

                generated_text="### 回答：\n\n根据国务院办公厅转发的《关于恢复和扩大消费的措施》通知，针对汽车购买使用管理，主要提出了以下政策：\n\n1. **优化汽车限购措施**：各地区不得新增汽车限购措施，对于已经实施限购的地区，应因地制宜优化汽车限购措施。\n\n2. **扩大新能源汽车消费**：落实构建高质量充电基础设施体系、支持新能源汽车下乡、延续和优化新能源汽车车辆购置税减免等政策。\n\n这些措施旨在通过优化限购政策、支持新能源汽车发展和消费，促进汽车市场的稳定和扩大，同时推动新能源汽车的普及和使用。"

                #generated_text = "根据检索到的文档，国家卫生健康委员会于2023年8月8日启动的“启明行动”活动，主要针对的是儿童青少年近视问题。这项活动旨在开展儿童眼保健、保护儿童视力健康的相关知识宣传和教育，通过多种渠道向公众传播开展儿童眼保健、保护儿童视力健康的重要意义。同时，活动强调医疗机构应重点面向儿童家长和养育人，提供个性化咨询指导，针对儿童常见眼病和近视防控等重点问题，通过面对面咨询指导，帮助儿童家长树立近视防控意识，改变不良生活方式，增加户外活动时间，培养良好的爱眼护眼习惯。\n\n这项活动的依据文件可能包括《防控儿童青少年近视核心知识十条》等指导性文件，旨在通过综合措施来预防和控制儿童青少年近视问题，促进儿童青少年的视力健康。"

                #generated_text = "根据您提供的信息，国家卫生健康委员会在2023年8月8日启动的“启明行动”活动，主要针对的是儿童青少年近视防控问题。这项活动依据的指导文件名称可能是《防控儿童青少年近视核心知识十条》。该文件旨在向公众传播开展儿童眼保健、保护儿童视力健康的重要意义，并普及预防近视的科学知识。通过社会宣传和健康教育，活动将强调儿童家长和养育人应提高近视防控意识，改变不良生活方式，增加户外活动时间，培养儿童形成良好的爱眼护眼习惯。同时，医疗机构将通过面对面咨询指导，为儿童家长提供个性化建议，以促进儿童青少年的视力健康。"

                #generated_text = "response> 国家卫生健康委员会于2023年7月28日启动的名为“启明行动”的专项活动，主要针对儿童青少年的近视防控健康问题。该活动所依据的指导性文件名称为《防控儿童青少年近视核心知识十条》。"

                #generated_text = "根据检索到的文档，国家卫生健康委员会于2023年8月8日启动了名为“启明行动”的专项活动，主要针对儿童青少年近视问题。这项活动旨在通过开展儿童青少年近视知识的宣传教育、视力筛查、提供视力保健服务等，以预防和控制儿童青少年近视。活动依据的指导文件名称为《防控儿童青少年近视核心知识十条》。"

                #generated_text = "\n\n回答：根据国家卫生健康委员会在2023年8月8日启动的“启明行动”活动，该活动主要针对儿童青少年视力健康问题。活动旨在通过社会宣传和健康教育，提高公众对儿童眼保健和保护视力健康的认识。具体措施包括：\n\n1. **社会宣传和健康教育**：通过网络、广播电视、报刊杂志、海报墙报、培训讲座等多种形式，普及儿童眼保健和视力保护的科学知识，特别是强调《防控儿童青少年近视核心知识十条》的重要性。\n\n2. **发放体育消费券**：上海市体育局联合美团、大众点评发放500万元的体育消费券，覆盖3000多家本地运动门店，提供不同面额的消费券供消费者领取，以促进体育消费和全民健身运动的热情。\n\n3. **成都体育消费促进活动**：成都市体育局利用成都大运会的契机，发放各类体育消费券和惠民运动券，通过举办主题体育消费促进活动，如“爱成都·迎大运”、“运动成都·悦动生活”等，促进体育消费持续增长。\n\n4. **体育消费平台建设**：成都计划通过举办大型体育展会活动，如中国（成都）生活体育大会、“巴山蜀水·运动川渝”体育旅游休闲消费季、世界赛事名城发展大会、中国国际体育用品博览会等，进一步推动“体育+会展+消费”平台建设，促进体育消费的提质扩容。\n\n5. **儿童青少年近视防控**：国家卫生健康委员会启动的“启明行动”活动，针对儿童青少年视力健康问题，通过开展儿童眼病筛查、视力检查等服务，提供专业指导和预防措施，旨在防控儿童青少年近视。\n\n这些活动和措施旨在通过多渠道、多形式的干预，提高公众对儿童青少年视力健康问题的认识，促进健康生活方式的形成，以及通过政策和经济激励手段，鼓励参与体育活动和预防近视，从而全面促进儿童青少年的视力健康。"

                #generated_text = "\n\n回答：根据国家卫生健康委员会在2023年8月8日启动的“启明行动”活动，该活动主要针对儿童青少年视力健康问题。活动旨在通过社会宣传和健康教育，提高公众对儿童眼保健和保护视力健康的认识。具体措施包括：\n\n1. **社会宣传与健康教育**：通过网络、广播电视、报刊杂志、海报墙报、培训讲座等多种形式，普及儿童眼保健和视力保护的重要性，重点宣传《防控儿童青少年近视核心知识十条》。\n\n2. **发放体育消费券**：上海市体育局联合美团和大众点评发放总额为500万元的体育消费券，覆盖3000多家本地运动门店，提供不同面额的消费券供消费者领取，以促进体育消费和全民健身运动。\n\n3. **成都体育消费促进活动**：成都市体育局利用成都大运会的契机，发放各类体育消费券和惠民运动券，同时计划通过举办大型体育展会活动和推动“体育+会展+消费”平台建设来促进体育消费的提质扩容。\n\n4. **儿童青少年视力健康活动**：国家卫生健康委员会启动的“启明行动”活动，针对儿童青少年视力健康问题，通过开展儿童眼病筛查、视力检查等服务，旨在防控儿童青少年近视，提供专业指导和干预措施。\n\n这些活动和措施旨在通过多渠道、多形式的宣传和实践，提高公众对儿童青少年视力健康问题的认识，促进健康生活方式的形成，以及提供必要的服务和资源，以有效防控和改善儿童青少年的视力健康状况。"

                #generated_text = "\n\n回答：根据国家卫生健康委员会在2023年8月8日启动的“启明行动”活动，该活动主要针对的是儿童青少年群体，旨在防控儿童青少年近视问题。活动内容包括开展社会宣传和健康教育，通过网络、广播电视、报刊杂志、海报墙报、培训讲座等多种形式，向社会公众传播儿童眼保健和保护视力健康的重要性。同时，活动强调普及预防近视的科学知识，如《防控儿童青少年近视核心知识十条》。\n\n在医疗机构层面，活动要求以儿童家长和养育人为重点，结合眼保健和眼科临床服务，提供个性化咨询指导，帮助家长和养育人树立近视防控意识，改变不良生活方式，鼓励儿童进行户外活动，培养良好的爱眼护眼习惯。\n\n此外，成都市体育局还利用成都大运会的契机，发放各类体育消费券和惠民运动券，通过举办大型体育展会活动和推动“体育+会展+消费”平台建设，进一步促进体育消费的提质扩容，以持续激发体育消费活力和增长潜力。\n\n综上所述，这些活动和措施旨在通过教育、政策支持和市场激励等多方面手段，共同促进儿童青少年的视力健康和体育活动参与，以预防近视和其他眼健康问题。"

                data["generated_text"] = generated_text
                print(f"generated_text = {generated_text}, \n\n\n\n retrieved_documents = {retrieved_documents}")
                result = {"id": data["ID"], **self.scoring(data)}
                print(f"\n\n\nresult = {result} \n")
                if contain_original_data:
                    result["original_data"] = data
                results.append(result)
            except Exception as e:
                print(repr(e))

        results = sorted(results, key=lambda x: x["id"]) if sort else results
        valid_results = self.remove_invalid(results)

        try:
            overall = self.compute_overall(valid_results) if len(valid_results) > 0 else {}
        except Exception as e:
            print(repr(e))
            overall = dict()

        output = {"overall": overall, "results": results}
        self.save_output(output)
        print(f"Output saved to {self.output_path}!")
        return output
