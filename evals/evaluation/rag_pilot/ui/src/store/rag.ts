// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { defineStore } from "pinia";

export const ragAppStore = defineStore("rag", {
  state: () => ({
    ragEndpoint: "",
  }),
  persist: {
    key: "rcrag",
    storage: localStorage,
  },
  actions: {
    setEndpointState(endpoint: string) {
      this.ragEndpoint = endpoint;
    },
  },
});
