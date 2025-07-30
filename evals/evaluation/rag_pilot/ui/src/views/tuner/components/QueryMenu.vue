<template>
  <div class="menu-flex">
    <a-affix :offset-top="180">
      <div class="query-list">
        <a-pagination
          v-if="queryList.length"
          v-model:current="currentIndex"
          :showSizeChanger="false"
          :total="listTotal"
          :pageSize="1"
          @change="handlePaginationChange"
        />
      </div>
    </a-affix>
  </div>
</template>

<script setup lang="ts" name="TunerProcess">
import { ref, computed, watch } from "vue";
import type { PropType } from "vue";
import type { ResultOut } from "../type";

const props = defineProps({
  menu: {
    type: Array as PropType<ResultOut[]>,
    required: true,
    default: () => [],
  },
  currentId: {
    type: [Number, null] as PropType<number | null>,
    default: null,
  },
});

const emit = defineEmits(["updateId", "switch"]);

const queryList = ref<ResultOut[]>([]);
const currentIndex = ref<number>(1);
const currentQuery = ref<number | null>(null);

const listTotal = computed(() => queryList.value.length);

const updateQueryMenu = (list: ResultOut[]) => {
  queryList.value = [...list];
  if (list.length && !currentQuery.value) {
    const firstId = list[0]?.query_id;
    currentQuery.value = firstId;
    emit("updateId", firstId);
  }
};

const updateCurrentQuery = (id: number | null) => {
  if (!id) return;
  currentQuery.value = id;
};

const handlePaginationChange = () => {
  emit("switch");
};

watch(
  () => props.menu,
  (newMenu) => {
    if (newMenu.length) {
      updateQueryMenu(newMenu);
    }
  },
  { immediate: true, deep: true }
);

watch(
  () => props.currentId,
  (newId) => {
    if (newId) {
      updateCurrentQuery(newId);
    }
  },
  { immediate: true }
);

watch(
  () => currentQuery.value,
  (newId) => {
    if (!newId) return;

    const index = queryList.value.findIndex((item) => item.query_id === newId);
    if (index >= 0) {
      currentIndex.value = index + 1;
    }
  },
  { immediate: true }
);

watch(
  () => currentIndex.value,
  (newIndex) => {
    if (!newIndex || !queryList.value.length) return;

    const item = queryList.value[newIndex - 1];
    if (item?.query_id && item.query_id !== currentQuery.value) {
      currentQuery.value = item.query_id;
      emit("updateId", item.query_id);
    }
  },
  { immediate: true }
);
</script>

<style lang="less" scoped>
.menu-flex {
  display: flex;
  position: relative;
  height: calc(100vh - 240px);
  width: 40px;
  left: -32px;
  .query-list {
    height: 100%;
    width: 48px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    .query-item {
      display: none !important;
      position: relative;
      width: 28px;
      height: 28px;
      border-radius: 50%;
      background-color: var(--color-switch-theme);
      margin-top: 12px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      .vertical-center;
      &:hover {
        color: var(--color-white);
        background-color: var(--color-primary-hover);
        box-shadow: 0px 1px 2px 0px var(--bg-box-shadow);
      }
      &.is-active {
        color: var(--color-white);
        background-color: var(--color-primary-tip);
      }
      .is-rated {
        position: absolute;
        top: -4px;
        right: -6px;
        color: var(--color-warning) !important;
        font-size: 16px;
      }
    }
  }
  .content-container {
    height: 100%;
    margin-left: 24px;
    flex: 1;
  }
}
:deep(.intel-pagination) {
  display: flex !important;
  flex-direction: column;
  gap: 12px;
  width: 32px;
  .intel-pagination-item {
    position: relative;
    width: 32px;
    height: 32px;
    min-width: 28px;
    line-height: 28px;
    border-radius: 50%;
    background-color: var(--color-switch-theme);
    border: 1px solid var(--color-switch-theme);
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    .vertical-center;
    &:hover {
      color: var(--color-white);
      background-color: var(--color-primary-hover);
      box-shadow: 0px 1px 2px 0px var(--bg-box-shadow);
    }
  }
  .intel-pagination-item-active {
    background-color: var(--color-primary-tip);
    a {
      color: var(--color-white);
    }
  }
  .intel-pagination-prev,
  .intel-pagination-jump-next,
  .intel-pagination-jump-prev,
  .intel-pagination-next {
    transform: rotate(90deg);
  }
}
@media (max-width: 960px) {
  .menu-flex {
    left: -6px;
  }
}
</style>
