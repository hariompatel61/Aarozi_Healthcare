import type { ComputedRef, MaybeRef } from "vue";
import type { ComponentProps } from "../../node_modules/vue-component-type-helpers/index.js";

declare module 'nuxt/app' {
  interface NuxtLayouts {
    auth: ComponentProps<typeof import("C:/Users/techn/Documents/Aarozi_Healthcare/apps/web/layouts/auth.vue").default>
    customer: ComponentProps<typeof import("C:/Users/techn/Documents/Aarozi_Healthcare/apps/web/layouts/customer.vue").default>
    default: ComponentProps<typeof import("C:/Users/techn/Documents/Aarozi_Healthcare/apps/web/layouts/default.vue").default>
    marketing: ComponentProps<typeof import("C:/Users/techn/Documents/Aarozi_Healthcare/apps/web/layouts/marketing.vue").default>
  }
  export type LayoutKey = keyof NuxtLayouts extends never ? string : keyof NuxtLayouts
  interface PageMeta {
    layout?: MaybeRef<LayoutKey | false> | ComputedRef<LayoutKey | false> | {
      [K in LayoutKey]: {
        name?: MaybeRef<K | false> | ComputedRef<K | false>
        props?: NuxtLayouts[K]
      }
    }[LayoutKey]
  }
}