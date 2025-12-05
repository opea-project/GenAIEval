// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { defineStore } from "pinia";

export const pipelineAppStore = defineStore("pipeline", {
  state: () => ({
    basePipeline: null,
  }),
  persist: {
    key: "pipelineInfo",
    storage: localStorage,
  },
  actions: {
    setPipeline(id: any) {
      this.basePipeline = id;
    },
  },
});
