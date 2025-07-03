<template>
  <div class="home-container">
    <div class="upload-container">
      <h1 class="title-wrap">{{ $t("home.title") }}</h1>
      <div class="des-wrap">
        {{ $t("home.des") }}
      </div>
      <div v-if="!activatedPipeline" class="warring-tip">
        <ExclamationCircleFilled />
        {{ $t("home.title") }}
      </div>
      <div class="add-wrap">
        <template v-if="isCreated">
          <div>
            <a-button type="primary" @click="handleEdit">
              <template #icon>
                <EditOutlined />
              </template>
              {{ $t("home.edit") }}</a-button
            >
            <a-button @click="handleDownload">
              <template #icon>
                <DownloadOutlined />
              </template>
              {{ $t("common.download") }}</a-button
            >
          </div></template
        >
        <a-button v-else type="primary" @click="handleCreate">
          <template #icon>
            <PlusOutlined />
          </template>
          {{ $t("home.create") }}</a-button
        >
      </div>
      <div class="upload-wrap">
        <a-upload-dragger
          v-model:fileList="queryFile"
          name="file"
          :action="uploadQueryFileUrl"
          accept=".csv,.json"
          :showUploadList="false"
          :before-upload="handleBeforeUploadQery"
          @change="handleUploadQeryChange"
        >
          <template v-if="queryUploaded">
            <CheckCircleFilled class="success-icon" />
            <p class="success-text">{{ $t("home.uploadSucc") }}</p>
          </template>
          <template v-else>
            <SvgIcon name="icon-cloudupload-fill" :size="50" />
            <p class="intel-upload-text">
              {{ $t("common.uploadTip") }}
            </p>
            <p class="intel-upload-hint">
              {{ $t("home.fileFormat") }}
            </p></template
          >
          <a-button type="primary" class="mt-12">{{
            queryUploaded ? "Re-upload" : "Upload"
          }}</a-button>
        </a-upload-dragger>
      </div>
      <div class="footer-wrap">
        <a-button
          class="reset-btn"
          :icon="h(RedoOutlined)"
          @click="handleReset"
          >{{ $t("common.reset") }}</a-button
        >
        <div>
          <span class="text-wrap" v-if="isCreated">
            <CheckCircleOutlined
              :style="{ fontSize: '16px', color: 'var(--color-success)' }"
            />
            {{ $t("home.created") }}</span
          >
          <a-button
            class="next-btn"
            type="primary"
            :disabled="!(btnDisabled || isCreated)"
            @click="handleNextStep"
            >{{ $t("common.next") }} <ArrowRightOutlined
          /></a-button>
        </div>
      </div>
    </div>
    <!-- EnterDrawer -->
    <EnterDrawer
      v-if="enterDrawer.visible"
      :form-data="enterDrawer.data"
      @update="handleUpdate"
      @close="enterDrawer.visible = false"
    />
  </div>
</template>

<script lang="ts" setup name="UploadFile">
import { getActivePipelineDetail, uploadQueryFileUrl } from "@/api/ragPilot";
import router from "@/router";
import { useNotification, downloadJson } from "@/utils/common";
import { NextLoading } from "@/utils/loading";
import EnterDrawer from "./components/EnterDrawer.vue";
import {
  RedoOutlined,
  ArrowRightOutlined,
  CheckCircleFilled,
  ExclamationCircleFilled,
  PlusOutlined,
  EditOutlined,
  DownloadOutlined,
  CheckCircleOutlined,
} from "@ant-design/icons-vue";
import { message, UploadProps } from "ant-design-vue";
import { h, ref } from "vue";
import { useI18n } from "vue-i18n";

const { t } = useI18n();
const { antNotification } = useNotification();
const queryFile = ref([]);
const queryUploaded = ref<boolean>(false);
const activatedPipeline = ref<boolean>(true);
const groundTruthData = reactive<EmptyObjectType>({});

const enterDrawer = reactive<DialogType>({
  data: {},
  visible: false,
});
const isCreated = computed(() => {
  return !!groundTruthData.groundtruths?.length;
});
const btnDisabled = computed(() => {
  return queryUploaded.value && activatedPipeline.value;
});

const handleBeforeUploadQery = (file: UploadProps["fileList"][number]) => {
  const isFileSize = file.size / 1024 / 1024 < 200;

  if (!isFileSize) {
    message.error(t("home.validSizeErr"));
  }

  return isFileSize;
};
const handleUploadQeryChange = (info: any) => {
  const el = <HTMLElement>document.querySelector(".loading-next");
  if (!el) NextLoading.start();
  try {
    const { response, status } = info.file;

    if (status === "done") {
      NextLoading.done();
      queryUploaded.value = true;
    } else if (status === "error") {
      NextLoading.done();
      antNotification("error", t("common.error"), response.detail);
    }
  } catch (error) {
    console.error(error);
    if (NextLoading) NextLoading.done();
  }
};
const queryActivePipeline = async () => {
  const data: any = await getActivePipelineDetail();

  activatedPipeline.value = !!data;
};
const handleReset = () => {
  queryFile.value = [];
  queryUploaded.value = false;
};
const handleNextStep = () => {
  router.push({ name: "Tuner" });
};

const handleCreate = () => {
  enterDrawer.visible = true;
  enterDrawer.data = {};
};

const handleEdit = () => {
  enterDrawer.visible = true;
  enterDrawer.data = groundTruthData;
};
const handleDownload = () => {
  downloadJson(groundTruthData?.groundtruths);
};

const handleUpdate = (data: EmptyObjectType) => {
  Object.assign(groundTruthData, data);
};
onMounted(() => {
  queryActivePipeline();
});
</script>

<style lang="less" scoped>
.home-container {
  .vertical-center-transform;
  width: 60%;
  max-width: 960px;
  min-width: 680px;
}
.upload-container {
  background-color: var(--bg-card-color);
  border-radius: 8px;
  margin: 0 auto;
  .p-24;
  .title-wrap {
    font-size: 36px;
    line-height: 56px;
    color: var(--font-main-color);
    font-weight: 500;
    width: 100%;
    text-align: center;
  }
  .des-wrap {
    font-size: 16px;
    line-height: 24px;
    width: 100%;
    text-align: center;
    padding-bottom: 16px;
  }
  .add-wrap {
    .flex-end;
    gap: 6px;
  }
  .upload-wrap {
    width: 100%;
    margin-top: 16px;
    :deep(.intel-upload-drag) {
      background-color: var(--bg-card-color);
    }
    .upload-title {
      font-size: 20px;
      color: var(--font-main-color);
      .mb-12;
      .flex-between;
      .radio-group {
        font-weight: 500;
      }
    }
    .success-icon {
      color: var(--color-success);
      font-size: 60px;
    }
    .success-text {
      .mt-12;
      font-size: 16px;
    }
  }
  .warring-tip {
    border: 1px solid var(--border-warning);
    background-color: var(--color-warningBg);
    color: var(--color-second-warning);
    padding: 8px 12px;
    border-radius: 4px;
    .flex-left;
    gap: 4px;
  }
  .footer-wrap {
    .flex-between;
    .mt-24;
    .reset-btn {
      .anticon {
        transform: rotate(-60deg);
      }
    }
    .text-wrap {
      margin-right: 8px;
      color: var(--font-tip-color);
      .anticon-info-circle {
        margin-right: 4px;
      }
    }
  }
}
</style>
