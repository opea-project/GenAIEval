// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createRouter, createWebHistory } from "vue-router";
import { notFoundRoute, routeList } from "./routes";

const router = createRouter({
  history: createWebHistory(),
  routes: [...notFoundRoute, ...routeList],
});

export default router;
