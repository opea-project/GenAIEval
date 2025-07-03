<template>
  <div class="generation-container">
    <GenerationResults
      v-if="showResults"
      :pipelines="pipelinesList"
      :results="resultsData"
      :base-result="baseResults"
      @back="showResults = false"
    />
    <Prompt v-else @next="showResults = true" :prompts="promptsList" />
  </div>
</template>

<script setup lang="ts" name="Generation">
import { ref, onMounted } from "vue";
import { GenerationResults, Prompt } from "./index";
import {
  getResultsByStage,
  requesStageRun,
  getStagePipelines,
  getResultsByPipelineId,
} from "@/api/ragPilot";
import { ResultOut } from "../type";
import { Local } from "@/utils/storage";

const showResults = ref<boolean>(false);
const intervalId = ref<any>(null);
const resultsData = ref<ResultOut[]>([]);
const pipelinesList = ref<EmptyArrayType>([]);
const promptsList = ref<EmptyArrayType>([]);
const basePipeline = ref<number | null>();
const baseResults = ref<ResultOut[]>([]);

const querypipelineIds = async () => {
  const data: any = await getStagePipelines("generation");

  const uniquePipelineIds = new Set();

  data.flat().forEach((item: any) => {
    if (!uniquePipelineIds.has(item.pipeline_id)) {
      uniquePipelineIds.add(item.pipeline_id);
      pipelinesList.value.push(item.pipeline_id);
      promptsList.value.push(item.targets["generator.prompt_content"]);
    }
  });
};

const queryResultsByStage = async () => {
  const data: any = (await getResultsByStage("generation")) || {};

  if (Object.keys(data).length) {
    const isFinished = Object.values(data).every(
      (item: any) => item?.finished === true
    );
    const isValid = Object.values(data).some(
      (item: any) => Array.isArray(item?.results) && item.results?.length > 0
    );

    if (isValid) {
      const { results = [] } = handleResultsData(data);
      resultsData.value = [].concat(results);
    }

    if (isFinished) {
      clearInterval(intervalId.value);
    }
  }
};
const handleResultsData = (originalData: Record<string, any>) => {
  const transformedResults: Record<string, any>[] = [];
  const pipelines = Object.keys(originalData);
  const firstKey = pipelines[0];
  const query_ids = originalData[firstKey]?.results.map(
    (item: any) => item?.query_id
  );

  query_ids?.forEach((query_id: any) => {
    const newItem: Record<string, any> = { query_id };

    Object.keys(originalData).forEach((key) => {
      const matchedItem = originalData[key]?.results.find(
        (item: any) => item?.query_id === query_id
      );
      if (matchedItem) {
        const {
          response = "",
          metadata: { answer_relevancy = 0 },
        } = matchedItem;
        newItem[key] = {
          response,
          metadata: { answer_relevancy },
        };

        Object.keys(matchedItem).forEach((prop) => {
          if (prop !== "query_id") {
            newItem[prop] = matchedItem[prop];
          }
        });
      }
    });

    transformedResults.push(newItem);
  });

  return { results: transformedResults };
};
const querysBaseResult = async () => {
  basePipeline.value = Local.get("pipelineInfo")?.basePipeline;
  if (basePipeline.value) {
    const data: any = (await getResultsByPipelineId(basePipeline.value!)) || [];
    const baseData = data?.results?.map((item: any) => {
      const {
        response = "",
        metadata: { answer_relevancy = 0 },
      } = item;
      return {
        ...item,
        base: {
          response,
          metadata: { answer_relevancy },
        },
      };
    });

    baseResults.value = [].concat(baseData);
  }
};
const handleGenerationRun = async () => {
  await requesStageRun("generation");
  querypipelineIds();
  intervalId.value = setInterval(() => queryResultsByStage(), 5000);
};
onMounted(() => {
  handleGenerationRun();
  querysBaseResult();
});
onUnmounted(() => {
  clearInterval(intervalId.value);
});
</script>

<style lang="less" scoped>
.generation-container {
  width: 100%;
  height: 100%;
  padding-bottom: 64px;
}
</style>
