<template>
  <div class="home-container">
    <div class="upload-container">
      <h1 class="title-wrap">{{ $t("home.title") }}</h1>
      <div class="des-wrap">
        {{ $t("home.des") }}
      </div>
      <div v-if="!activatedPipeline" class="warring-tip">
        <ExclamationCircleFilled />
        {{ $t("home.tip") }}
      </div>
      <div class="body-wrap">
        <a-card hoverable>
          <template #cover>
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
                <div class="top-wrap">
                  <template v-if="queryUploaded">
                    <div class="icon-wrap is-success">
                      <SvgIcon
                        name="icon-results"
                        :size="32"
                        :style="{ color: 'var(--color-success)' }"
                      />
                    </div>
                    <h2>{{ $t("home.uploadSucc") }}</h2>
                  </template>
                  <template v-else>
                    <div class="icon-wrap">
                      <SvgIcon
                        name="icon-upload1"
                        :size="32"
                        :style="{ color: 'var(--color-primary)' }"
                      />
                    </div>
                    <h2>{{ $t("home.upload") }}</h2>
                  </template>
                  <p>
                    {{ $t("common.uploadTip") }}, {{ $t("home.fileFormat") }}
                  </p>
                </div>
                <div class="bottom-wrap">
                  <a-button
                    type="primary"
                    :icon="
                      h(queryUploaded ? FileSyncOutlined : CloudUploadOutlined)
                    "
                    class="button-wrap"
                  >
                    {{
                      $t(queryUploaded ? "common.reUpload" : "common.upload")
                    }}</a-button
                  >
                  <p class="text-wrap">{{ $t("home.sizeFormat") }}</p>
                </div>
              </a-upload-dragger>
            </div>
          </template>
        </a-card>
        <a-card hoverable>
          <template #cover>
            <div class="upload-wrap">
              <div class="top-wrap">
                <template v-if="isCreated">
                  <div class="icon-wrap is-success">
                    <SvgIcon
                      name="icon-results"
                      :size="32"
                      :style="{ color: 'var(--color-success)' }"
                    />
                  </div>
                  <h2>{{ $t("home.created") }}</h2>
                </template>
                <template v-else>
                  <div class="icon-wrap">
                    <SvgIcon
                      name="icon-edit"
                      :size="32"
                      :style="{ color: 'var(--color-primary)' }"
                    />
                  </div>
                  <h2>{{ $t("home.manual") }}</h2>
                </template>
                <p>
                  {{ $t("home.createdText") }}
                </p>
              </div>
              <div class="bottom-wrap">
                <div v-if="isCreated" class="edit-wrap">
                  <a-button
                    type="primary"
                    :icon="h(EditOutlined)"
                    @click="handleEdit"
                  >
                    {{ $t("home.edit") }}</a-button
                  >
                  <a-button
                    type="primary"
                    :icon="h(DownloadOutlined)"
                    ghost
                    @click="handleDownload"
                  >
                    {{ $t("common.download") }}</a-button
                  >
                </div>
                <a-button
                  v-else
                  type="primary"
                  :icon="h(PlusOutlined)"
                  class="button-wrap"
                  @click="handleCreate"
                >
                  {{ $t("home.create") }}</a-button
                >
                <p class="text-wrap">{{ $t("home.createdTip") }}</p>
              </div>
            </div>
          </template>
        </a-card>
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
import {
  getActivePipelineDetail,
  uploadQueryFileUrl,
  requestPipelineReset,
} from "@/api/ragPilot";
import router from "@/router";
import { useNotification, downloadJson } from "@/utils/common";
import { NextLoading } from "@/utils/loading";
import EnterDrawer from "./components/EnterDrawer.vue";
import {
  RedoOutlined,
  ArrowRightOutlined,
  ExclamationCircleFilled,
  PlusOutlined,
  EditOutlined,
  DownloadOutlined,
  CheckCircleOutlined,
  FileSyncOutlined,
  CloudUploadOutlined,
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
const handlePipelineReset = async () => {
  await requestPipelineReset();
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
  handlePipelineReset();
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
    padding-bottom: 32px;
  }
  .tip-wrap {
    font-size: 12px;
    color: var(--font-tip-color);
    text-align: center;
    padding-bottom: 16px;
  }

  .body-wrap {
    .flex-between;
    .mt-16;
    gap: 24px;

    .intel-card {
      flex: 1;
      :deep(.intel-upload-btn) {
        padding: 0;
      }
      .top-wrap {
        background-color: var(--color-second-primaryBg);
        padding: 20px;
        height: 210px;
        .icon-wrap {
          width: 64px;
          height: 64px;
          border-radius: 50%;
          background-color: var(--color-primaryBg);
          margin: 0 auto;
          .vertical-center;
          &.is-success {
            background-color: var(--color-successBg);
          }
        }
      }
      .bottom-wrap {
        padding: 16px;
        .button-wrap {
          width: 100%;
          height: 38px;
          .vertical-center;
          .icon-intel {
            margin-right: 8px;
          }
        }
        .text-wrap {
          color: var(--font-tip-color);
          font-size: 12px;
          .mt-12;
        }
        .edit-wrap {
          .flex-between;
          .intel-btn {
            flex: 1;
          }
        }
      }
    }
  }
  .upload-wrap {
    width: 100%;
    text-align: center;
    padding: 1px;
    border-radius: 8px;
    overflow: hidden;
    :deep(.intel-upload-drag) {
      background-color: var(--bg-content-color);
      border: none;
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
      font-size: 32px;
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
    padding: 4px 12px;
    border-radius: 4px;
    .flex-left;
    .mb-12;
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
