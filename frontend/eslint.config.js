// @ts-check
const eslint = require("@eslint/js");
const tseslint = require("typescript-eslint");
const angular = require("angular-eslint");

module.exports = tseslint.config(
  { ignores: ["dist/**", ".angular/**", "node_modules/**"] },
  {
    files: ["**/*.ts"],
    extends: [
      eslint.configs.recommended,
      ...tseslint.configs.recommended,
      ...tseslint.configs.stylistic,
      ...angular.configs.tsRecommended,
    ],
    processor: angular.processInlineTemplates,
    rules: {
      // Código limpio
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/consistent-type-assertions": ["error", { assertionStyle: "as", objectLiteralTypeAssertions: "never" }],
      eqeqeq: ["error", "always"],
      "no-console": ["error", { allow: ["warn", "error"] }],
      "prefer-const": "error",
      complexity: ["warn", 12],
      "max-depth": ["warn", 3],
      "max-lines-per-function": ["warn", { max: 60, skipBlankLines: true, skipComments: true }],
      // Seguridad: nada de ejecutar texto ni de saltarse el saneado de Angular
      "no-eval": "error",
      "no-implied-eval": "error",
      "no-new-func": "error",
      "no-script-url": "error",
      "no-restricted-properties": [
        "error",
        { object: "document", property: "write", message: "document.write abre la puerta a XSS." },
        { property: "outerHTML", message: "Usa plantillas de Angular: escapan el contenido por defecto." },
        { property: "insertAdjacentHTML", message: "Usa plantillas de Angular: escapan el contenido por defecto." },
      ],
      "no-restricted-syntax": [
        "error",
        {
          selector: "AssignmentExpression[left.property.name='innerHTML']",
          message: "No asignes innerHTML: usa plantillas de Angular.",
        },
        {
          selector: "CallExpression[callee.property.name=/^bypassSecurityTrust/]",
          message: "bypassSecurityTrust* desactiva el saneado de Angular y no está permitido.",
        },
      ],
      "@angular-eslint/directive-selector": [
        "error",
        {
          type: "attribute",
          prefix: "app",
          style: "camelCase",
        },
      ],
      "@angular-eslint/component-selector": [
        "error",
        {
          type: "element",
          prefix: "app",
          style: "kebab-case",
        },
      ],
    },
  },
  {
    files: ["**/*.html"],
    extends: [
      ...angular.configs.templateRecommended,
      ...angular.configs.templateAccessibility,
    ],
    rules: {
      "@angular-eslint/template/no-any": "error",
      "@angular-eslint/template/eqeqeq": "error",
      "@angular-eslint/template/no-inline-styles": "off",
      "@angular-eslint/template/prefer-control-flow": "error",
      "@angular-eslint/template/button-has-type": "error",
    },
  },
  {
    // En las pruebas se permiten funciones largas (describe) y aserciones sobre objetos literales.
    files: ["**/*.spec.ts", "src/testing/**"],
    rules: {
      "max-lines-per-function": "off",
      "@typescript-eslint/consistent-type-assertions": "off",
      "no-script-url": "off", // las pruebas usan «javascript:» como entrada hostil a propósito
    },
  }
);
