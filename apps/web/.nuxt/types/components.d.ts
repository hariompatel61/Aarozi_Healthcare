
import type { DefineComponent, SlotsType } from 'vue'
type IslandComponent<T> = DefineComponent<{}, {refresh: () => Promise<void>}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, SlotsType<{ fallback: { error: unknown } }>> & T

type HydrationStrategies = {
  hydrateOnVisible?: IntersectionObserverInit | true
  hydrateOnIdle?: number | true
  hydrateOnInteraction?: keyof HTMLElementEventMap | Array<keyof HTMLElementEventMap> | true
  hydrateOnMediaQuery?: string
  hydrateAfter?: number
  hydrateWhen?: boolean
  hydrateNever?: true
}
type LazyComponent<T> = DefineComponent<HydrationStrategies, {}, {}, {}, {}, {}, {}, { hydrated: () => void }> & T

interface _GlobalComponents {
  ShellCommandPalette: typeof import("../../components/shell/CommandPalette.vue")['default']
  ShellSidebar: typeof import("../../components/shell/Sidebar.vue")['default']
  ShellTopHeader: typeof import("../../components/shell/TopHeader.vue")['default']
  UiBadge: typeof import("../../components/ui/Badge.vue")['default']
  UiButton: typeof import("../../components/ui/Button.vue")['default']
  UiCard: typeof import("../../components/ui/Card.vue")['default']
  UiCheckbox: typeof import("../../components/ui/Checkbox.vue")['default']
  UiChip: typeof import("../../components/ui/Chip.vue")['default']
  UiConfirmDialog: typeof import("../../components/ui/ConfirmDialog.vue")['default']
  UiDataTable: typeof import("../../components/ui/DataTable.vue")['default']
  UiDrawer: typeof import("../../components/ui/Drawer.vue")['default']
  UiEmptyState: typeof import("../../components/ui/EmptyState.vue")['default']
  UiFilterBar: typeof import("../../components/ui/FilterBar.vue")['default']
  UiFormField: typeof import("../../components/ui/FormField.vue")['default']
  UiIcon: typeof import("../../components/ui/Icon.vue")['default']
  UiIconButton: typeof import("../../components/ui/IconButton.vue")['default']
  UiInput: typeof import("../../components/ui/Input.vue")['default']
  UiKbd: typeof import("../../components/ui/Kbd.vue")['default']
  UiModal: typeof import("../../components/ui/Modal.vue")['default']
  UiNumberInput: typeof import("../../components/ui/NumberInput.vue")['default']
  UiPageHeader: typeof import("../../components/ui/PageHeader.vue")['default']
  UiPaginationBar: typeof import("../../components/ui/PaginationBar.vue")['default']
  UiSearchField: typeof import("../../components/ui/SearchField.vue")['default']
  UiSegmentedControl: typeof import("../../components/ui/SegmentedControl.vue")['default']
  UiSelect: typeof import("../../components/ui/Select.vue")['default']
  UiSkeleton: typeof import("../../components/ui/Skeleton.vue")['default']
  UiStatCard: typeof import("../../components/ui/StatCard.vue")['default']
  UiSwitch: typeof import("../../components/ui/Switch.vue")['default']
  UiTabs: typeof import("../../components/ui/Tabs.vue")['default']
  UiToast: typeof import("../../components/ui/Toast.vue")['default']
  UiToastProvider: typeof import("../../components/ui/ToastProvider.vue")['default']
  NuxtWelcome: typeof import("../../node_modules/nuxt/dist/app/components/welcome.vue")['default']
  NuxtLayout: typeof import("../../node_modules/nuxt/dist/app/components/nuxt-layout")['default']
  NuxtErrorBoundary: typeof import("../../node_modules/nuxt/dist/app/components/nuxt-error-boundary.vue")['default']
  ClientOnly: typeof import("../../node_modules/nuxt/dist/app/components/client-only")['default']
  DevOnly: typeof import("../../node_modules/nuxt/dist/app/components/dev-only")['default']
  ServerPlaceholder: typeof import("../../node_modules/nuxt/dist/app/components/server-placeholder")['default']
  NuxtLink: typeof import("../../node_modules/nuxt/dist/app/components/nuxt-link")['default']
  NuxtLoadingIndicator: typeof import("../../node_modules/nuxt/dist/app/components/nuxt-loading-indicator")['default']
  NuxtTime: typeof import("../../node_modules/nuxt/dist/app/components/nuxt-time.vue")['default']
  NuxtRouteAnnouncer: typeof import("../../node_modules/nuxt/dist/app/components/nuxt-route-announcer")['default']
  NuxtAnnouncer: typeof import("../../node_modules/nuxt/dist/app/components/nuxt-announcer")['default']
  NuxtImg: typeof import("../../node_modules/nuxt/dist/app/components/nuxt-stubs")['NuxtImg']
  NuxtPicture: typeof import("../../node_modules/nuxt/dist/app/components/nuxt-stubs")['NuxtPicture']
  NuxtPage: typeof import("../../node_modules/nuxt/dist/pages/runtime/page")['default']
  NoScript: typeof import("../../node_modules/nuxt/dist/head/runtime/components")['NoScript']
  Link: typeof import("../../node_modules/nuxt/dist/head/runtime/components")['Link']
  Base: typeof import("../../node_modules/nuxt/dist/head/runtime/components")['Base']
  Title: typeof import("../../node_modules/nuxt/dist/head/runtime/components")['Title']
  Meta: typeof import("../../node_modules/nuxt/dist/head/runtime/components")['Meta']
  Style: typeof import("../../node_modules/nuxt/dist/head/runtime/components")['Style']
  Head: typeof import("../../node_modules/nuxt/dist/head/runtime/components")['Head']
  Html: typeof import("../../node_modules/nuxt/dist/head/runtime/components")['Html']
  Body: typeof import("../../node_modules/nuxt/dist/head/runtime/components")['Body']
  NuxtIsland: typeof import("../../node_modules/nuxt/dist/app/components/nuxt-island")['default']
  LazyShellCommandPalette: LazyComponent<typeof import("../../components/shell/CommandPalette.vue")['default']>
  LazyShellSidebar: LazyComponent<typeof import("../../components/shell/Sidebar.vue")['default']>
  LazyShellTopHeader: LazyComponent<typeof import("../../components/shell/TopHeader.vue")['default']>
  LazyUiBadge: LazyComponent<typeof import("../../components/ui/Badge.vue")['default']>
  LazyUiButton: LazyComponent<typeof import("../../components/ui/Button.vue")['default']>
  LazyUiCard: LazyComponent<typeof import("../../components/ui/Card.vue")['default']>
  LazyUiCheckbox: LazyComponent<typeof import("../../components/ui/Checkbox.vue")['default']>
  LazyUiChip: LazyComponent<typeof import("../../components/ui/Chip.vue")['default']>
  LazyUiConfirmDialog: LazyComponent<typeof import("../../components/ui/ConfirmDialog.vue")['default']>
  LazyUiDataTable: LazyComponent<typeof import("../../components/ui/DataTable.vue")['default']>
  LazyUiDrawer: LazyComponent<typeof import("../../components/ui/Drawer.vue")['default']>
  LazyUiEmptyState: LazyComponent<typeof import("../../components/ui/EmptyState.vue")['default']>
  LazyUiFilterBar: LazyComponent<typeof import("../../components/ui/FilterBar.vue")['default']>
  LazyUiFormField: LazyComponent<typeof import("../../components/ui/FormField.vue")['default']>
  LazyUiIcon: LazyComponent<typeof import("../../components/ui/Icon.vue")['default']>
  LazyUiIconButton: LazyComponent<typeof import("../../components/ui/IconButton.vue")['default']>
  LazyUiInput: LazyComponent<typeof import("../../components/ui/Input.vue")['default']>
  LazyUiKbd: LazyComponent<typeof import("../../components/ui/Kbd.vue")['default']>
  LazyUiModal: LazyComponent<typeof import("../../components/ui/Modal.vue")['default']>
  LazyUiNumberInput: LazyComponent<typeof import("../../components/ui/NumberInput.vue")['default']>
  LazyUiPageHeader: LazyComponent<typeof import("../../components/ui/PageHeader.vue")['default']>
  LazyUiPaginationBar: LazyComponent<typeof import("../../components/ui/PaginationBar.vue")['default']>
  LazyUiSearchField: LazyComponent<typeof import("../../components/ui/SearchField.vue")['default']>
  LazyUiSegmentedControl: LazyComponent<typeof import("../../components/ui/SegmentedControl.vue")['default']>
  LazyUiSelect: LazyComponent<typeof import("../../components/ui/Select.vue")['default']>
  LazyUiSkeleton: LazyComponent<typeof import("../../components/ui/Skeleton.vue")['default']>
  LazyUiStatCard: LazyComponent<typeof import("../../components/ui/StatCard.vue")['default']>
  LazyUiSwitch: LazyComponent<typeof import("../../components/ui/Switch.vue")['default']>
  LazyUiTabs: LazyComponent<typeof import("../../components/ui/Tabs.vue")['default']>
  LazyUiToast: LazyComponent<typeof import("../../components/ui/Toast.vue")['default']>
  LazyUiToastProvider: LazyComponent<typeof import("../../components/ui/ToastProvider.vue")['default']>
  LazyNuxtWelcome: LazyComponent<typeof import("../../node_modules/nuxt/dist/app/components/welcome.vue")['default']>
  LazyNuxtLayout: LazyComponent<typeof import("../../node_modules/nuxt/dist/app/components/nuxt-layout")['default']>
  LazyNuxtErrorBoundary: LazyComponent<typeof import("../../node_modules/nuxt/dist/app/components/nuxt-error-boundary.vue")['default']>
  LazyClientOnly: LazyComponent<typeof import("../../node_modules/nuxt/dist/app/components/client-only")['default']>
  LazyDevOnly: LazyComponent<typeof import("../../node_modules/nuxt/dist/app/components/dev-only")['default']>
  LazyServerPlaceholder: LazyComponent<typeof import("../../node_modules/nuxt/dist/app/components/server-placeholder")['default']>
  LazyNuxtLink: LazyComponent<typeof import("../../node_modules/nuxt/dist/app/components/nuxt-link")['default']>
  LazyNuxtLoadingIndicator: LazyComponent<typeof import("../../node_modules/nuxt/dist/app/components/nuxt-loading-indicator")['default']>
  LazyNuxtTime: LazyComponent<typeof import("../../node_modules/nuxt/dist/app/components/nuxt-time.vue")['default']>
  LazyNuxtRouteAnnouncer: LazyComponent<typeof import("../../node_modules/nuxt/dist/app/components/nuxt-route-announcer")['default']>
  LazyNuxtAnnouncer: LazyComponent<typeof import("../../node_modules/nuxt/dist/app/components/nuxt-announcer")['default']>
  LazyNuxtImg: LazyComponent<typeof import("../../node_modules/nuxt/dist/app/components/nuxt-stubs")['NuxtImg']>
  LazyNuxtPicture: LazyComponent<typeof import("../../node_modules/nuxt/dist/app/components/nuxt-stubs")['NuxtPicture']>
  LazyNuxtPage: LazyComponent<typeof import("../../node_modules/nuxt/dist/pages/runtime/page")['default']>
  LazyNoScript: LazyComponent<typeof import("../../node_modules/nuxt/dist/head/runtime/components")['NoScript']>
  LazyLink: LazyComponent<typeof import("../../node_modules/nuxt/dist/head/runtime/components")['Link']>
  LazyBase: LazyComponent<typeof import("../../node_modules/nuxt/dist/head/runtime/components")['Base']>
  LazyTitle: LazyComponent<typeof import("../../node_modules/nuxt/dist/head/runtime/components")['Title']>
  LazyMeta: LazyComponent<typeof import("../../node_modules/nuxt/dist/head/runtime/components")['Meta']>
  LazyStyle: LazyComponent<typeof import("../../node_modules/nuxt/dist/head/runtime/components")['Style']>
  LazyHead: LazyComponent<typeof import("../../node_modules/nuxt/dist/head/runtime/components")['Head']>
  LazyHtml: LazyComponent<typeof import("../../node_modules/nuxt/dist/head/runtime/components")['Html']>
  LazyBody: LazyComponent<typeof import("../../node_modules/nuxt/dist/head/runtime/components")['Body']>
  LazyNuxtIsland: LazyComponent<typeof import("../../node_modules/nuxt/dist/app/components/nuxt-island")['default']>
}

declare module 'vue' {
  export interface GlobalComponents extends _GlobalComponents { }
}

export {}
