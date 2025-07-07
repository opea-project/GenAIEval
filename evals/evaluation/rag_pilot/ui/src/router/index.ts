// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createRouter, createWebHashHistory } from "vue-router";
import { notFoundRoute, routeList } from "./routes";

const router = createRouter({
  history: createWebHashHistory(),
  routes: [...notFoundRoute, ...routeList],
});

export default router;
