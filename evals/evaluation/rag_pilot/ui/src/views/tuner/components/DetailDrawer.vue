<template>
  <a-drawer
    v-model:open="drawerVisible"
    :title="$t('pipeline.detail')"
    destroyOnClose
    width="500px"
    @close="handleClose"
  >
    <!-- Node Parser -->
    <div class="module-wrap">
      <a-collapse v-model:activeKey="nodeParserActive" expandIconPosition="end">
        <a-collapse-panel key="nodeParser" :header="$t('pipeline.nodeParser')">
          <ul class="form-wrap">
            <li
              class="item-wrap"
              v-if="formData.node_parser?.direct?.chunk_size"
            >
              <span class="label-wrap"> {{ $t("pipeline.chunkSize") }}</span>
              <span class="content-wrap">{{
                formData.node_parser?.direct.chunk_size
              }}</span>
            </li>
            <li
              class="item-wrap"
              v-if="formData.node_parser?.direct?.chunk_overlap"
            >
              <span class="label-wrap">{{ $t("pipeline.chunkOverlap") }}</span>
              <span class="content-wrap">{{
                formData.node_parser.direct.chunk_overlap
              }}</span>
            </li>
          </ul>
        </a-collapse-panel>
      </a-collapse>
    </div>
    <!-- Indexer -->
    <div class="module-wrap">
      <a-collapse v-model:activeKey="indexerActive" expandIconPosition="end">
        <a-collapse-panel key="indexer" :header="$t('pipeline.indexer')">
          <ul class="form-wrap">
            <li
              class="item-wrap"
              v-if="formData.indexer?.embedding_model?.model_name"
            >
              <span class="label-wrap">{{ $t("pipeline.embedding") }}</span>
              <span class="content-wrap">{{
                formData.indexer.embedding_model.model_name
              }}</span>
            </li>
          </ul>
        </a-collapse-panel>
      </a-collapse>
    </div>
    <!-- Retriever -->
    <div class="module-wrap">
      <a-collapse v-model:activeKey="retrieverActive" expandIconPosition="end">
        <a-collapse-panel key="retriever" :header="$t('pipeline.retriever')">
          <ul class="form-wrap">
            <li
              class="item-wrap"
              v-if="formData.retriever?.vectorsimilarity?.top_k"
            >
              <span class="label-wrap">{{ $t("pipeline.topk") }}</span>
              <span class="content-wrap">{{
                formData.retriever.vectorsimilarity.top_k
              }}</span>
            </li>
          </ul>
        </a-collapse-panel>
      </a-collapse>
    </div>
    <!-- PostProcessor -->
    <div class="module-wrap">
      <a-collapse
        v-model:activeKey="postProcessorActive"
        expandIconPosition="end"
      >
        <a-collapse-panel
          key="postProcessor"
          :header="$t('pipeline.postProcessor')"
        >
          <ul class="form-wrap">
            <li
              class="item-wrap"
              v-if="formData.postprocessor?.reranker?.model_name"
            >
              <span class="label-wrap">{{ $t("pipeline.rerank") }}</span>
              <span class="content-wrap">{{
                formData.postprocessor.reranker.model_name
              }}</span>
            </li>
            <li
              class="item-wrap"
              v-if="formData.postprocessor?.reranker?.top_n"
            >
              <span class="label-wrap">{{ $t("pipeline.top_n") }}</span>
              <span class="content-wrap">{{
                formData.postprocessor.reranker.top_n
              }}</span>
            </li>
          </ul>
        </a-collapse-panel>
      </a-collapse>
    </div>
  </a-drawer>
</template>
<script lang="ts" setup name="DetailDrawer">
import { computed, reactive, ref } from "vue";

const props = defineProps({
  drawerData: {
    type: Object,
    required: true,
    default: () => {},
  },
});
const emit = defineEmits(["close"]);
const formData = reactive<EmptyObjectType>(props.drawerData);
const drawerVisible = ref<boolean>(true);
const nodeParserActive = ref<string>("nodeParser");
const indexerActive = ref<string>("indexer");
const retrieverActive = ref<string>("retriever");
const postProcessorActive = ref<string>("postProcessor");
const generatorActive = ref<string>("generator");

const isHierarchical = computed(() => {
  return formData.node_parser.parser_type === "hierarchical";
});
const isSentencewindow = computed(() => {
  return formData.node_parser.parser_type === "sentencewindow";
});
const handleClose = () => {
  emit("close");
};
</script>
<style scoped lang="less">
.basic-wrap {
  .basic-item {
    display: flex;
    gap: 12px;
    margin: 0;
    line-height: 24px;
    .content-wrap {
      color: var(--font-main-color);
      font-weight: 600;
    }
    .active-state {
      color: var(--color-success);
    }
  }
}
.module-wrap {
  margin-top: 20px;
  .intel-collapse {
    border-color: var(--border-main-color);
    :deep(.intel-collapse-header) {
      padding: 8px 16px;
    }
    :deep(.intel-collapse-header-text) {
      .fs-14;
      font-weight: 600;
      color: var(--font-main-color);
    }

    :deep(.intel-collapse-item) {
      border-bottom: 1px solid var(--border-main-color);
    }

    :deep(.intel-collapse-content) {
      border-top: 1px solid var(--border-main-color);
      .intel-collapse-content-box {
        padding: 10px 16px;
      }
    }
  }
  .form-wrap {
    padding: 0;
    margin: 0;
    .item-wrap {
      list-style: none;
      display: flex;
      gap: 12px;
      line-height: 1.2;
      padding: 6px 0;
      display: flex;
      color: var(--font-text-color);
      word-wrap: break-word;
      .content-wrap {
        color: var(--font-main-color);
        font-weight: 500;
        display: inline-flex;
        align-items: baseline;
        justify-content: end;
        flex: 1;
        word-break: break-word;
        overflow-wrap: break-word;
      }
    }
    &.bt-border {
      border-top: 1px dashed var(--border-main-color);
    }
  }
}
.label-wrap {
  position: relative;
  &::after {
    content: ":";
    .ml-2;
  }
}
</style>
