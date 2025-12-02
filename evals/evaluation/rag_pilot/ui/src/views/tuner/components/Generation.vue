<template>
  <div class="generation-container">
    <GenerationResults
      v-if="showResults"
      :pipelines="pipelinesList"
      :results="resultsData"
      :base-result="baseResults"
      @back="handleBack"
      @exit="handleExit"
    />
    <Prompt
      v-else
      :prompts="promptsList"
      :loading="promptLoad"
      :inProgress
      :isInit
      @run="handleRun"
      @exit="handleExit"
      @next="showResults = true"
    />
  </div>
</template>

<script setup lang="ts" name="Generation">
import { ref, onMounted } from "vue";
import { GenerationResults, Prompt } from "./index";
import {
  getResultsByStage,
  requestStageRun,
  getStagePipelines,
  getResultsByPipelineId,
  getPromptlById,
  requestStageReset,
  requestPipelineRun,
  getTunerEffectiveConfiguration,
} from "@/api/ragPilot";
import { ResultOut } from "../type";
import { Modal } from "ant-design-vue";
import { useI18n } from "vue-i18n";
import { pipelineAppStore } from "@/store/pipeline";
import router from "@/router";
const { t } = useI18n();
const pipelineStore = pipelineAppStore();

const showResults = ref<boolean>(false);
const isInit = ref<boolean>(true);
const intervalId = ref<any>(null);
const intervalBaseId = ref<any>(null);
const resultsData = ref<ResultOut[]>([]);
const pipelinesList = ref<EmptyArrayType>([]);
const promptsList = ref<EmptyArrayType>([]);
const basePipeline = ref<number | null>();
const baseResults = ref<ResultOut[]>([]);
const promptLoad = ref<boolean>(false);
const inProgress = ref<boolean>(false);
const stageList = ref<string[]>(["retrieval", "postprocessing", "generation"]);

const queryPipelineIds = async () => {
  try {
    const [stageData, baseData]: [any, any] = await Promise.all([
      getStagePipelines("generation"),
      getPromptlById(basePipeline.value!),
    ]);
    const uniquePipelineIds = new Set();

    stageData.flat().forEach((item: any) => {
      if (!uniquePipelineIds.has(item.pipeline_id)) {
        uniquePipelineIds.add(item.pipeline_id);

        pipelinesList.value.push(item.pipeline_id);
        pipelinesList.value = [...new Set(pipelinesList.value)];

        promptsList.value.push(item.targets["generator.prompt.content"]);
        promptsList.value = [...new Set(promptsList.value)];
      }
    });
    promptsList.value.unshift(baseData || "");
    promptLoad.value = false;
  } catch (err) {
    console.log(err);
  }
};

const queryGenerationPrompts = async () => {
  try {
    const [stageData, baseData]: [any, any] = await Promise.all([
      getTunerEffectiveConfiguration(),
      getPromptlById(basePipeline.value!),
    ]);

    const stageTuners = stageData.flatMap((item: any) =>
      item.stage === "generation" ? item.tuners : []
    );

    stageTuners?.forEach((tuner: any) => {
      tuner.modules?.forEach((module: any) => {
        if (module.type === "prompt") {
          module.attributes?.forEach((attr: any) => {
            if (attr.params?.values) {
              attr.params.values.forEach((value: any) => {
                promptsList.value.push(value);
              });
            }
          });
        }
      });
    });
    promptsList.value.unshift(baseData || "");
    promptLoad.value = false;
  } catch (err) {
    console.log(err);
  }
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
      inProgress.value = false;
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
const queryBaseResult = async () => {
  if (basePipeline.value) {
    const data: any = (await getResultsByPipelineId(basePipeline.value!)) || [];
    if (!data?.results) {
      handleSpecialBaseResult();
      return;
    }
    handleGenerationRun();
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
const handleSpecialBaseResult = async () => {
  try {
    await requestPipelineRun(basePipeline.value!);
    getBaseResult();
    queryGenerationPrompts();
    intervalBaseId.value = setInterval(getBaseResult, 5000);
  } catch (err) {
    console.error(err);
    inProgress.value = false;
  }
};
const getBaseResult = async () => {
  const data: any = (await getResultsByPipelineId(basePipeline.value!)) || [];
  if (data?.results?.length) {
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
  if (data?.finished) {
    clearInterval(intervalBaseId.value);
    handleGenerationRun();
  }
};

const handleRun = async () => {
  promptsList.value = [];
  pipelinesList.value = [];
  promptLoad.value = true;
  inProgress.value = true;

  queryBaseResult();
};
const handleGenerationRun = async () => {
  try {
    await requestStageRun("generation");
    await queryPipelineIds();

    intervalId.value = setInterval(() => queryResultsByStage(), 5000);
  } catch (error) {
    promptLoad.value = false;
    inProgress.value = false;
  }
};
const handleReset = async () => {
  try {
    const promises = stageList.value.map((stage) => requestStageReset(stage));
    await Promise.all(promises);
    pipelineStore.setPipeline("");
  } catch (err) {
    console.log(err);
  }
};
const handleExit = () => {
  Modal.confirm({
    title: t("common.prompt"),
    content: t("common.exitTip"),
    okText: t("common.confirm"),
    async onOk() {
      await handleReset();
      router.push({ name: "Home" });
    },
  });
};
const handleBack = () => {
  showResults.value = false;
  isInit.value = false;
};
onMounted(() => {
  basePipeline.value = pipelineStore.basePipeline;
});
onUnmounted(() => {
  clearInterval(intervalId.value);
  clearInterval(intervalBaseId.value);
});
</script>

<style lang="less" scoped>
.generation-container {
  width: 100%;
  height: 100%;
  padding-bottom: 64px;
}
</style>
