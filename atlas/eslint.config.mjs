// ESLint 9 flat config for the atlas.
//
// Uses FlatCompat from @eslint/eslintrc to load `eslint-config-next`
// (which still ships in legacy .eslintrc format) and extends two of
// its presets: core-web-vitals for React/Next rules, and typescript
// for @typescript-eslint rules tuned to Next.js conventions.
//
// The `ignores` block is load-bearing: without it, ESLint walks the
// .next/dev/ build output and reports tens of thousands of warnings
// from Next.js's own generated code. node_modules/ and public/ are
// also excluded so the scan focuses on source files only.

import { dirname } from "path";
import { fileURLToPath } from "url";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

const eslintConfig = [
  {
    ignores: [
      ".next/**",
      "node_modules/**",
      "public/**",
      "out/**",
      "dist/**",
      "next-env.d.ts",
    ],
  },
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    // Honor the underscore-prefix convention for intentionally unused
    // variables and parameters. Without this override, the
    // @typescript-eslint/no-unused-vars rule flags `_id` and `_colleges`
    // even though the underscore is the signal that the value is
    // deliberately unused (e.g., a placeholder callback parameter, a
    // prop kept in the type for future use).
    rules: {
      "@typescript-eslint/no-unused-vars": [
        "error",
        {
          argsIgnorePattern: "^_",
          varsIgnorePattern: "^_",
          caughtErrorsIgnorePattern: "^_",
        },
      ],
    },
  },
];

export default eslintConfig;
