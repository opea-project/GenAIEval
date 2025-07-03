// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { inject } from "vue";
import { customNotification } from "./notification";

export const useNotification = () => {
  const customNotificationInjected =
    inject<typeof customNotification>("customNotification");

  if (!customNotificationInjected) {
    throw new Error("Notification service not provided");
  }
  return {
    antNotification: customNotificationInjected,
  };
};

export const formatDecimals = (num: number, decimalPlaces: number = 2) => {
  const factor = Math.pow(10, decimalPlaces);
  return Math.round(num * factor) / factor;
};

export const formatPercentage = (
  value: number,
  precision: number = 2
): string => {
  const num = value * 100;
  return `${num.toFixed(precision)}%`;
};

export const formatCapitalize = (
  string: string,
  start: number = 0,
  length: number = 1
) => {
  const end = start + length;
  const part1 = string.slice(0, start);
  const part2 = string.slice(start, end).toUpperCase();
  const part3 = string.slice(end);
  return part1 + part2 + part3;
};

/**
 * Convert text to uppercase letters
 * * @param preserveSpaces keep consecutive spaces
 * * @param keepOriginalCase Maintain non initial capitalization
 */
export const formatTextStrict = (
  str: string,
  options?: {
    preserveSpaces?: boolean;
    keepOriginalCase?: boolean;
  }
): string => {
  const { preserveSpaces = true, keepOriginalCase = false } = options || {};

  // replace _ and -
  let processed = str.replace(/[_-]/g, " ");

  if (!preserveSpaces) {
    processed = processed.replace(/\s+/g, " ");
  }
  return processed
    .split(preserveSpaces ? /(\s+)/ : /\s+/)
    .map((segment) => {
      if (segment.trim() === "") {
        return segment;
      }
      const firstChar = segment.charAt(0).toUpperCase();
      const restChars = keepOriginalCase
        ? segment.slice(1)
        : segment.slice(1).toLowerCase();
      return firstChar + restChars;
    })
    .join("");
};

export const transformTunerName = (name: String) => {
  let result = name.replace(/Tuner/g, "");
  result = result.replace(/([A-Z])/g, " $1").trim();

  return result;
};

/**
 * @param data
 * @param filename
 */
export const downloadJson = (
  data: object | string,
  filename: string = "ground_truth.json"
) => {
  const jsonStr: string =
    typeof data === "string" ? data : JSON.stringify(data, null, 2);

  const blob: Blob = new Blob([jsonStr], { type: "application/json" });

  const url: string = URL.createObjectURL(blob);

  const a: HTMLAnchorElement = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();

  // 清理
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};
