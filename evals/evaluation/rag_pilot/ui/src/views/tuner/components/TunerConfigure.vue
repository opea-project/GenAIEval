<template>
  <a-drawer
    v-model:open="drawerVisible"
    :title="$t('tuner.configure')"
    destroyOnClose
    :closable="false"
    @close="handleClose"
    :width="700"
  >
    <div class="body-container">
      <div class="configure-container" ref="rightContentRef">
        <div class="title-wrap">
          <span>{{ $t("tuner.select") }} </span>
          <a-upload
            v-model:fileList="tunerFile"
            name="file"
            accept=".json"
            :showUploadList="false"
            :before-upload="handleBeforeUpload"
          >
            <a-tooltip
              placement="top"
              arrow-point-at-center
              :title="$t('tuner.fileFormat')"
            >
              <a-button type="primary" :icon="h(CloudUploadOutlined)">
                {{ $t("tuner.import") }}
              </a-button></a-tooltip
            >
          </a-upload>
        </div>
        <div class="selectors">
          <div class="selector-row" v-for="top in tunersList" :key="top.id">
            <div class="selector-title">{{ top.label }}</div>
            <div class="chips">
              <a-space wrap>
                <div
                  v-for="sec in top.items"
                  :key="sec.id"
                  :class="{
                    'tuner-name': true,
                    'selected-item': selectedSecondIds.has(sec.id),
                  }"
                  @click="handleTunerClick(sec.id)"
                >
                  <span class="active-icon" v-if="selectedSecondIds.has(sec.id)"
                    ><CheckOutlined :style="{ fontSize: '8px' }"
                  /></span>
                  {{ sec.label }}
                </div>
              </a-space>
            </div>
          </div>
        </div>
        <div class="cards-container">
          <template v-for="top in tunersList" :key="top.id">
            <template v-for="sec in top.items" :key="sec.id">
              <div
                v-if="selectedSecondIds.has(sec.id)"
                :id="sec.id"
                class="tuner-card"
              >
                <div class="card-header">
                  <div class="flex-left">
                    <div class="card-title">{{ sec.label }}</div>
                    <div class="card-sub" size="small">{{ top.label }}</div>
                  </div>
                  <a-space>
                    <a-button
                      danger
                      size="small"
                      @click="handleTunerDelete(sec.id)"
                    >
                      {{ $t("common.delete") }}
                    </a-button>
                  </a-space>
                </div>
                <div class="module-wrap">
                  <div class="module-row" v-if="sec.modules?.length">
                    <div class="module-title">{{ $t("tuner.module") }} :</div>
                    <a-space>
                      <div v-for="module in sec.modules" :key="module.id">
                        <a-tag
                          :color="
                            isModuleSelected(sec.id, module.id)
                              ? 'processing'
                              : undefined
                          "
                          @click="handleModuleSelection(sec.id, module.id)"
                        >
                          {{ module.name }}
                        </a-tag>
                      </div>
                    </a-space>
                  </div>
                  <div
                    v-if="!selectedModuleIdsPerSec[sec.id]?.length"
                    class="no-tuner"
                  >
                    {{ $t("tuner.notModule") }}
                  </div>
                  <div v-if="sec.modules && sec.modules.length">
                    <template v-for="module in sec.modules" :key="module.id">
                      <div
                        v-show="isModuleSelected(sec.id, module.id)"
                        class="module-attrs"
                      >
                        <div class="module-attrs-header flex-between">
                          <span
                            >{{ module.name }}
                            <span
                              v-if="!parameterHasAnySelection(module)"
                              class="warn-tip"
                            >
                              <ExclamationCircleOutlined />
                              {{ $t("tuner.notOption") }}
                            </span>
                          </span>
                          <DeleteFilled
                            @click="handleModuleSelection(sec.id, module.id)"
                          />
                        </div>
                        <div
                          v-for="option in module.options"
                          :key="option.id"
                          class="options-wrap"
                        >
                          <div class="option-body">
                            <a-checkbox-group
                              :value="option.selectedValues"
                              @change="(value:any) => handleOptionChange(option, value as any[])"
                            >
                              <a-checkbox
                                v-for="v in option.values"
                                :key="String(v)"
                                :value="v"
                              >
                                <span class="label-wrap"> {{ v }}</span>
                              </a-checkbox>
                            </a-checkbox-group>
                            <a-tooltip
                              placement="top"
                              arrow-point-at-center
                              :title="$t('tuner.add')"
                            >
                              <a-button
                                type="primary"
                                ghost
                                :icon="h(PlusOutlined)"
                                size="small"
                                class="ml-10"
                                @click="handleOptionAdd(option)"
                              >
                              </a-button
                            ></a-tooltip>
                          </div>
                        </div>
                      </div>
                    </template>
                  </div>
                </div>
              </div>
            </template>
          </template>
          <a-empty
            v-if="!selectedSecondIds.size"
            class="mt-100"
            :description="$t('tuner.notTunerTip')"
          />
        </div>
      </div>
    </div>
    <template #footer>
      <div class="flex-between">
        <a-button @click="handleClose">{{ $t("common.cancel") }}</a-button>
        <span>
          <a-button
            type="primary"
            ghost
            :icon="h(CloudDownloadOutlined)"
            @click="handleDownload"
          >
            {{ $t("tuner.export") }}</a-button
          >
          <a-button type="primary" @click="handleConfirm"
            >{{ $t("common.run") }}
          </a-button></span
        >
      </div>
    </template>
    <!-- Add Value Modal -->
    <a-modal
      v-model:open="addModalVisible"
      :title="$t('tuner.add')"
      @ok="handleAddOption"
      @cancel="handleCancelAdd"
    >
      <div style="display: flex; flex-direction: column; gap: 8px">
        <a-input
          v-model:value="addModalValue"
          :placeholder="$t('tuner.addPlaceholder')"
        />
      </div>
    </a-modal>
  </a-drawer>
</template>

<script setup lang="ts">
import { ref, h, onMounted } from "vue";
import {
  DeleteFilled,
  CheckOutlined,
  PlusOutlined,
  ExclamationCircleOutlined,
  CloudUploadOutlined,
  CloudDownloadOutlined,
} from "@ant-design/icons-vue";
import {
  downloadJson,
  formatTextStrict,
  useNotification,
} from "@/utils/common";

import {
  requestTunerRegister,
  getTunerAllConfiguration,
  getTunerEffectiveConfiguration,
} from "@/api/ragPilot";
import { useI18n } from "vue-i18n";

const { t } = useI18n();
const props = defineProps({
  stage: {
    type: String,
    default: "",
    required: true,
  },
});

type RawAttribute = {
  type: string;
  params?: { values?: any[]; [k: string]: any };
};

type RawModule = { type: string; attributes?: RawAttribute[] };

type RawTuner = {
  type: string;
  params?: { name?: string; [k: string]: any };
  modules?: RawModule[];
};

type ConfigOption = {
  id: string;
  label: string;
  values: any[];
  selectedValues: any[];
  type?: string;
};

type ModuleItem = {
  id: string;
  name: string;
  options: ConfigOption[];
  type?: string;
};

type SecondItem = {
  id: string;
  label: string;
  modules: ModuleItem[];
  raw?: RawTuner;
};

type TopItem = { id: string; label: string; items: SecondItem[] };
const emit = defineEmits(["close", "confirm"]);

const drawerVisible = ref(true);
const tunerFile = ref([]);
const { antNotification } = useNotification();

const allList = ref<RawTuner[]>([]);
const effectiveList = ref<RawTuner[]>([]);

const uid = (prefix = "") =>
  `${prefix}${Date.now().toString(36)}${Math.random()
    .toString(36)
    .slice(2, 8)}`;

const createConfigOption = (
  attr: RawAttribute,
  moduleId: string,
  index: number,
  baseVals: any[],
  selectedVals: any[]
): ConfigOption => {
  const optId = `${moduleId}-option-${attr.type ?? index}`;
  return {
    id: optId,
    label: attr.type,
    values: baseVals,
    selectedValues: selectedVals,
    type: attr.type,
  };
};

const findDefAttribute = (
  defMatch: RawTuner,
  moduleType: string,
  attrType: string
): RawAttribute | undefined => {
  const defModuleCandidates = (defMatch.modules || []).filter(
    (dm) => dm.type === moduleType
  );
  
  for (const dm of defModuleCandidates) {
    const foundDefAttr = (dm.attributes || []).find(
      (a) => a.type === attrType
    );
    if (foundDefAttr) return foundDefAttr;
  }
  return undefined;
};

const createModuleItem = (
  module: any,
  secId: string,
  attributes: RawAttribute[],
  defMatch: RawTuner | undefined
): ModuleItem[] => {
  return attributes.map((attr, index) => {
    const moduleId = `${secId}-${attr.type}`;
    const baseVals = Array.isArray(attr.params?.values)
      ? [...attr.params.values]
      : [];

    let selectedVals: any[] = [];
    let effectiveVals: any[] = [];
    
    if (defMatch) {
      const foundDefAttr = findDefAttribute(defMatch, module.type, attr.type);
      if (foundDefAttr && Array.isArray(foundDefAttr.params?.values)) {
        selectedVals = [...foundDefAttr.params.values];
        effectiveVals = [...foundDefAttr.params.values];
      }
    }

    const allValues = Array.from(new Set([...baseVals, ...effectiveVals]));
    
    const option = createConfigOption(attr, moduleId, index, allValues, selectedVals);
    
    return {
      id: moduleId,
      name: formatTextStrict(attr.type),
      options: [option],
      type: module.type,
    };
  });
};

const createSecondItem = (
  tuner: RawTuner,
  topKey: string,
  index: number,
  defMatch: RawTuner | undefined
): SecondItem => {
  const secId = `${topKey}-${tuner.params?.name ?? uid("sec_")}`;
  
  const modules: ModuleItem[] = [];
  (tuner.modules || []).forEach((module) => {
    const attrs = module.attributes || [];
    const moduleItems = createModuleItem(module, secId, attrs, defMatch);
    modules.push(...moduleItems);
  });

  return {
    id: secId,
    label: tuner.params?.name ?? `${tuner.type}-${index}`,
    raw: tuner,
    modules,
  };
};

const convertAllToInternal = (
  all: RawTuner[],
  registered: RawTuner[]
): TopItem[] => {
  const map = new Map<string, TopItem>();
  const defIndex = new Map<string, RawTuner>();
  
  registered.forEach((d) =>
    defIndex.set(`${d.type}-${d.params?.name ?? ""}`, d)
  );

  all.forEach((tuner, index) => {
    const topKey = tuner.type;
    
    if (!map.has(topKey)) {
      map.set(topKey, {
        id: topKey,
        label: formatTextStrict(topKey),
        items: [],
      });
    }
    
    const top = map.get(topKey)!;
    const defMatch = defIndex.get(`${tuner.type}-${tuner.params?.name ?? ""}`);
    
    const secondItem = createSecondItem(tuner, topKey, index, defMatch);
    top.items.push(secondItem);
  });

  return Array.from(map.values());
};

const tunersList = ref<TopItem[]>([]);
const selectedSecondIds = ref<Set<string>>(new Set());
const focusedSecondId = ref<string | null>(null);
const selectedModuleIdsPerSec = ref<Record<string, string[]>>({});
const rightContentRef = ref<HTMLElement | null>(null);

const initializeSelectionState = () => {
  effectiveList.value?.forEach((selected) => {
    const key = `${selected.type}-${selected.params?.name ?? ""}`;
    for (const tuner of tunersList.value) {
      const exactMatch = tuner.items.find((i) => i.id === key);
      if (exactMatch) {
        selectedSecondIds.value.add(exactMatch.id);
        continue;
      }
      
      const nameMatch = tuner.items.find((i) => i.label === selected.params?.name);
      if (nameMatch) selectedSecondIds.value.add(nameMatch.id);
    }
  });
};

const getSelectedModuleIds = (module: SecondItem, defMatch: RawTuner | undefined): string[] => {
  const selectedModuleIds: string[] = [];
  
  if (defMatch) {
    const defAttrsByType = new Set<string>();
    (defMatch.modules || []).forEach((dm) => {
      (dm.attributes || []).forEach((a) => {
        if (a.type) defAttrsByType.add(a.type);
      });
    });

    for (const m of module.modules || []) {
      const option = m.options?.[0];
      if (option && option.type && defAttrsByType.has(option.type)) {
        selectedModuleIds.push(m.id);
      }
    }
  }

  if (selectedModuleIds.length === 0 && module.modules?.length) {
    selectedModuleIds.push(module.modules[0].id);
  }

  return selectedModuleIds;
};

const setupModuleSelection = () => {
  for (const tuner of tunersList.value) {
    for (const module of tuner.items) {
      if (!selectedSecondIds.value.has(module.id)) continue;

      const defMatch = effectiveList.value.find(
        (selected) => selected.params?.name === module.label && selected.type === tuner.id
      );

      const selectedModuleIds = getSelectedModuleIds(module, defMatch);
      selectedModuleIdsPerSec.value[module.id] = selectedModuleIds;
    }
  }
};

const initSelectedFromDefault = () => {
  selectedSecondIds.value.clear();

  if (!effectiveList.value.length) return;

  initializeSelectionState();
  
  setupModuleSelection();

  const firstSelected = Array.from(selectedSecondIds.value.values())[0];
  focusedSecondId.value = firstSelected ?? null;
};

const handleTunerClick = (secId: string) => {
  if (selectedSecondIds.value.has(secId)) {
    selectedSecondIds.value.delete(secId);
    delete selectedModuleIdsPerSec.value[secId];
    if (focusedSecondId.value === secId) {
      const remain = Array.from(selectedSecondIds.value.values());
      focusedSecondId.value = remain.length ? remain[0] : null;
    }
  } else {
    selectedSecondIds.value.add(secId);
    const sec = findSecById(secId);
    selectedModuleIdsPerSec.value[secId] = sec?.modules?.length
      ? sec.modules.map((item) => item.id)
      : [];
    focusedSecondId.value = secId;
  }
};

const handleModuleSelection = (secId: string, moduleId: string) => {
  const arr = selectedModuleIdsPerSec.value[secId] ?? [];
  const idx = arr.indexOf(moduleId);
  if (idx >= 0) arr.splice(idx, 1);
  else arr.push(moduleId);
  selectedModuleIdsPerSec.value[secId] = arr;
};

const isModuleSelected = (secId: string, moduleId: string): boolean => {
  return (selectedModuleIdsPerSec.value[secId] ?? []).includes(moduleId);
};

const handleOptionChange = (option: ConfigOption, vals: any[]) => {
  option.selectedValues = vals;
};

const addModalVisible = ref(false);
const addModalValue = ref("");
const addModalTargetOpt = ref<ConfigOption | null>(null);

const handleOptionAdd = (option: ConfigOption) => {
  addModalTargetOpt.value = option;
  addModalValue.value = "";
  addModalVisible.value = true;
};

const handleCancelAdd = () => {
  addModalVisible.value = false;
  addModalValue.value = "";
  addModalTargetOpt.value = null;
};

const handleAddOption = async (): Promise<void> => {
  if (!addModalTargetOpt.value) {
    addModalVisible.value = false;
    return;
  }

  const option = addModalTargetOpt.value;
  const vRaw = (addModalValue.value ?? "").trim();

  if (!vRaw) return;

  let v: any = vRaw;
  if (option.values.length > 0 && typeof option.values[0] === "number") {
    const num = Number(vRaw);
    if (!Number.isNaN(num)) v = num;
  }

  if (!option.values.includes(v)) option.values.push(v);
  if (!option.selectedValues.includes(v)) option.selectedValues.push(v);

  addModalVisible.value = false;
  addModalValue.value = "";
  addModalTargetOpt.value = null;
};

const parameterHasAnySelection = (module: ModuleItem): boolean => {
  if (!module || !module.options) return false;
  return module.options.some(
    (option) =>
      Array.isArray(option.selectedValues) && option.selectedValues.length > 0
  );
};

const handleTunerDelete = (secId: string) => {
  if (selectedSecondIds.value.has(secId)) selectedSecondIds.value.delete(secId);

  if (secId in selectedModuleIdsPerSec.value)
    delete selectedModuleIdsPerSec.value[secId];
  if (focusedSecondId.value === secId) {
    const remain = Array.from(selectedSecondIds.value.values());
    focusedSecondId.value = remain.length ? remain[0] : null;
  }
};

const findSecById = (secId: string): SecondItem | undefined => {
  for (const tuner of tunersList.value!) {
    const s = tuner.items.find((i) => i.id === secId);
    if (s) return s;
  }
  return undefined;
};

const formatFormParam = () => {
  const tuners: RawTuner[] = [];
  tunersList.value?.forEach((top) => {
    top.items.forEach((sec) => {
      if (!selectedSecondIds.value.has(sec.id)) return;

      const baseRaw: RawTuner = sec.raw
        ? JSON.parse(JSON.stringify(sec.raw))
        : { type: top.id, params: { name: sec.label }, modules: [] };

      const modulesByType = new Map<string, RawModule>();

      (sec.modules || []).forEach((m) => {
        const selectedModuleIds = selectedModuleIdsPerSec.value[sec.id] ?? [];
        if (!selectedModuleIds.includes(m.id)) return;
        const type = m.type ?? m.name ?? "module";
        if (!modulesByType.has(type)) {
          modulesByType.set(type, {
            type: type,
            attributes: [],
          });
        }
        const rawModule = modulesByType.get(type)!;

        const option = m.options?.[0];
        if (option) {
          rawModule.attributes!.push({
            type: option.type ?? option.label,
            params: {
              values: Array.isArray(option.selectedValues)
                ? [...option.selectedValues]
                : [],
            },
          } as RawAttribute);
        }
      });

      baseRaw.modules = Array.from(modulesByType.values());
      tuners.push(baseRaw);
    });
  });
  const { stage } = props;
  return {
    stage,
    tuners,
  };
};

const handleBeforeUpload = (file: File) => {
  const isJson = file.type === "application/json" || /\.json$/i.test(file.name);
  if (!isJson) {
    antNotification("error", t("common.error"), t("tuner.validTypeErr"));

    return false;
  }

  if (file.size / 1024 / 1024 > 20) {
    antNotification("error", t("common.error"), t("tuner.validSizeErr"));

    return false;
  }

  const reader = new FileReader();
  reader.onload = (ev) => {
    try {
      const text = ev.target?.result;
      if (typeof text !== "string") {
        antNotification("error", t("common.error"), t("tuner.validDataErr"));
        return;
      }
      const parsed = JSON.parse(text);
      if (!parsed.tuners || !parsed.tuners.length) {
        antNotification("error", t("common.error"), t("tuner.validDataErr"));
        return;
      }
      effectiveList.value = [].concat(parsed.tuners);

      tunersList.value = convertAllToInternal(
        allList.value,
        effectiveList.value
      );
      initSelectedFromDefault();
    } catch (err: any) {
      antNotification("error", t("common.error"), err);
    }
  };
  reader.onerror = (err) => {
    console.error("File read error", err);
  };
  reader.readAsText(file, "utf-8");
  return false;
};

const handleClose = () => {
  emit("close");
};

const handleConfirm = async () => {
  try {
    await requestTunerRegister(formatFormParam());
    emit("confirm");
  } catch (err) {
    console.log(err);
  }
};

const handleDownload = () => {
  downloadJson(formatFormParam(), "tuners-configuration.json");
};

const queryTunerConfiguration = async () => {
  try {
    const { stage } = props;

    const [allConfiguration, effectiveConfiguration]: [any, any] =
      await Promise.all([
        getTunerAllConfiguration(),
        getTunerEffectiveConfiguration(),
      ]);

    allList.value = allConfiguration.flatMap((item: any) =>
      item.stage === stage ? item.tuners : []
    );
    effectiveList.value = effectiveConfiguration.flatMap((item: any) =>
      item.stage === stage ? item.tuners : []
    );

    tunersList.value = convertAllToInternal(allList.value, effectiveList.value);
    initSelectedFromDefault();
  } catch (err) {
    console.log(err);
  }
};

onMounted(() => {
  queryTunerConfiguration();
});
</script>

<style lang="less" scoped>
.body-container {
  height: 100%;

  .configure-container {
    .title-wrap {
      font-size: 18px;
      font-weight: 600;
      color: var(--font-main-color);
      margin-bottom: 12px;
      .flex-between;
    }
    .selectors {
      .selector-row {
        margin-bottom: 12px;
        .flex-left;
        gap: 16px;

        .selector-title {
          font-weight: 600;
          margin-bottom: 6px;
          width: 90px;
        }
        .chips {
          margin-bottom: 6px;
          .tuner-name {
            border: 1px solid var(--border-main-color);
            background-color: var(--bg-main-color);
            color: var(--font-text-color);
            cursor: pointer;
            border-radius: 4px;
            padding: 4px 0;
            font-size: 12px;
            position: relative;
            width: 160px;
            text-align: center;
            &:hover {
              border-color: var(--color-primary);
              color: var(--color-primary);
            }
            &.selected-item {
              border-color: var(--color-primary);
              color: var(--color-primary);
              background-color: var(--color-primaryBg);
            }
            .active-icon {
              position: absolute;
              right: -1px;
              top: -1px;
              border-radius: 0 4px 0 4px;
              width: 12px;
              height: 12px;
              background-color: var(--color-success);
              color: var(--color-white);
              .vertical-center;
            }
          }
        }
      }
    }

    .cards-container {
      .tuner-card {
        border: 1px solid var(--border-main-color);
        border-radius: 8px;
        margin-bottom: 12px;
        overflow: hidden;

        .card-header {
          .flex-between;
          border-bottom: 1px solid var(--border-main-color);
          background-color: var(--bg-second-color);
          padding: 6px 12px;

          .card-title {
            font-weight: 600;
          }
          .card-sub {
            color: var(--color-purple);
            background-color: var(--border-purple);
            padding: 2px 6px;
            border-radius: 8px;
            margin-left: 8px;
            font-size: 12px;
            line-height: 14px;
          }
        }
        .module-wrap {
          padding: 12px;
          background-color: var(--bg-main-color);
          .module-row {
            margin-bottom: 8px;

            .module-title {
              display: inline-block;
              margin-right: 8px;
              font-weight: 600;
            }
            .intel-tag {
              cursor: pointer;
            }
          }

          .module-attrs {
            margin: 8px 0 12px;
            border: 1px solid var(--border-main-color);
            border-radius: 6px;
            background-color: var(--bg-content-color);

            .module-attrs-header {
              padding: 4px 12px;
              font-weight: 600;
              margin-bottom: 6px;
              border-bottom: 1px solid var(--border-main-color);
              background-color: var(--bg-second-color);
              .anticon-delete {
                cursor: pointer;
                color: var(--font-tip-color);
                &:hover {
                  color: var(--color-error);
                }
              }
              .warn-tip {
                color: var(--color-error);
                font-size: 12px;
                font-weight: 400;
                .ml-8;
              }
            }
            .options-wrap {
              padding: 6px;
              .option-body {
                padding: 6px;
                .add-value {
                  margin-top: 8px;
                }
                :deep(.intel-checkbox-group) {
                  margin-bottom: 8px;
                }
                .label-wrap {
                  white-space: break-spaces;
                }
              }
            }
          }
        }
      }
    }
  }
}

.no-tuner {
  padding: 10px;
  border: 1px dashed var(--border-main-color);
  border-radius: 6px;
  color: var(--font-tip-color);
  margin: 8px 0;
  text-align: center;
}
</style>
