import { marked } from "marked";
import hljs from "highlight.js";
import { formatCapitalize } from "./common";

interface CodeRenderParams {
  text: string;
  lang?: string;
}

const renderer = new marked.Renderer();

renderer.link = ({ href, title, text }) => {
  return `<a href="${href}" target="_blank" rel="noopener noreferrer" ${
    title ? `title="${title}"` : ""
  }>${text}</a>`;
};

renderer.code = ({ text, lang }: CodeRenderParams) => {
  const language = hljs.getLanguage(lang || "") ? lang : "plaintext";
  const codeTitle = formatCapitalize(language || "Code");
  const codeHtml = hljs.highlight(text, {
    language: language || "plaintext",
  }).value;

  return `
    <div class="intel-highlighter">
      <div class="header-wrap">
        <span class="code-title">${codeTitle}</span>
      </div>
      <pre class="content-wrap"><div>${codeHtml}</div></pre>
    </div>
  `;
};

export default renderer;
