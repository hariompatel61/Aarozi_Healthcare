
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


export const ShellCommandPalette: typeof import("../components/shell/CommandPalette.vue")['default']
export const ShellSidebar: typeof import("../components/shell/Sidebar.vue")['default']
export const ShellTopHeader: typeof import("../components/shell/TopHeader.vue")['default']
export const UiBadge: typeof import("../components/ui/Badge.vue")['default']
export const UiButton: typeof import("../components/ui/Button.vue")['default']
export const UiCard: typeof import("../components/ui/Card.vue")['default']
export const UiCheckbox: typeof import("../components/ui/Checkbox.vue")['default']
export const UiChip: typeof import("../components/ui/Chip.vue")['default']
export const UiConfirmDialog: typeof import("../components/ui/ConfirmDialog.vue")['default']
export const UiDataTable: typeof import("../components/ui/DataTable.vue")['default']
export const UiDrawer: typeof import("../components/ui/Drawer.vue")['default']
export const UiEmptyState: typeof import("../components/ui/EmptyState.vue")['default']
export const UiFilterBar: typeof import("../components/ui/FilterBar.vue")['default']
export const UiFormField: typeof import("../components/ui/FormField.vue")['default']
export const UiIcon: typeof import("../components/ui/Icon.vue")['default']
export const UiIconButton: typeof import("../components/ui/IconButton.vue")['default']
export const UiInput: typeof import("../components/ui/Input.vue")['default']
export const UiKbd: typeof import("../components/ui/Kbd.vue")['default']
export const UiModal: typeof import("../components/ui/Modal.vue")['default']
export const UiNumberInput: typeof import("../components/ui/NumberInput.vue")['default']
export const UiPageHeader: typeof import("../components/ui/PageHeader.vue")['default']
export const UiPaginationBar: typeof import("../components/ui/PaginationBar.vue")['default']
export const UiSearchField: typeof import("../components/ui/SearchField.vue")['default']
export const UiSegmentedControl: typeof import("../components/ui/SegmentedControl.vue")['default']
export const UiSelect: typeof import("../components/ui/Select.vue")['default']
export const UiSkeleton: typeof import("../components/ui/Skeleton.vue")['default']
export const UiStatCard: typeof import("../components/ui/StatCard.vue")['default']
export const UiSwitch: typeof import("../components/ui/Switch.vue")['default']
export const UiTabs: typeof import("../components/ui/Tabs.vue")['default']
export const UiToast: typeof import("../components/ui/Toast.vue")['default']
export const UiToastProvider: typeof import("../components/ui/ToastProvider.vue")['default']
export const NuxtWelcome: typeof import("../node_modules/nuxt/dist/app/components/welcome.vue")['default']
export const NuxtLayout: typeof import("../node_modules/nuxt/dist/app/components/nuxt-layout")['default']
export const NuxtErrorBoundary: typeof import("../node_modules/nuxt/dist/app/components/nuxt-error-boundary.vue")['default']
export const ClientOnly: typeof import("../node_modules/nuxt/dist/app/components/client-only")['default']
export const DevOnly: typeof import("../node_modules/nuxt/dist/app/components/dev-only")['default']
export const ServerPlaceholder: typeof import("../node_modules/nuxt/dist/app/components/server-placeholder")['default']
export const NuxtLink: typeof import("../node_modules/nuxt/dist/app/components/nuxt-link")['default']
export const NuxtLoadingIndicator: typeof import("../node_modules/nuxt/dist/app/components/nuxt-loading-indicator")['default']
export const NuxtTime: typeof import("../node_modules/nuxt/dist/app/components/nuxt-time.vue")['default']
export const NuxtRouteAnnouncer: typeof import("../node_modules/nuxt/dist/app/components/nuxt-route-announcer")['default']
export const NuxtAnnouncer: typeof import("../node_modules/nuxt/dist/app/components/nuxt-announcer")['default']
export const NuxtImg: typeof import("../node_modules/nuxt/dist/app/components/nuxt-stubs")['NuxtImg']
export const NuxtPicture: typeof import("../node_modules/nuxt/dist/app/components/nuxt-stubs")['NuxtPicture']
export const NuxtPage: typeof import("../node_modules/nuxt/dist/pages/runtime/page")['default']
export const NoScript: typeof import("../node_modules/nuxt/dist/head/runtime/components")['NoScript']
export const Link: typeof import("../node_modules/nuxt/dist/head/runtime/components")['Link']
export const Base: typeof import("../node_modules/nuxt/dist/head/runtime/components")['Base']
export const Title: typeof import("../node_modules/nuxt/dist/head/runtime/components")['Title']
export const Meta: typeof import("../node_modules/nuxt/dist/head/runtime/components")['Meta']
export const Style: typeof import("../node_modules/nuxt/dist/head/runtime/components")['Style']
export const Head: typeof import("../node_modules/nuxt/dist/head/runtime/components")['Head']
export const Html: typeof import("../node_modules/nuxt/dist/head/runtime/components")['Html']
export const Body: typeof import("../node_modules/nuxt/dist/head/runtime/components")['Body']
export const NuxtIsland: typeof import("../node_modules/nuxt/dist/app/components/nuxt-island")['default']
export const LazyShellCommandPalette: LazyComponent<typeof import("../components/shell/CommandPalette.vue")['default']>
export const LazyShellSidebar: LazyComponent<typeof import("../components/shell/Sidebar.vue")['default']>
export const LazyShellTopHeader: LazyComponent<typeof import("../components/shell/TopHeader.vue")['default']>
export const LazyUiBadge: LazyComponent<typeof import("../components/ui/Badge.vue")['default']>
export const LazyUiButton: LazyComponent<typeof import("../components/ui/Button.vue")['default']>
export const LazyUiCard: LazyComponent<typeof import("../components/ui/Card.vue")['default']>
export const LazyUiCheckbox: LazyComponent<typeof import("../components/ui/Checkbox.vue")['default']>
export const LazyUiChip: LazyComponent<typeof import("../components/ui/Chip.vue")['default']>
export const LazyUiConfirmDialog: LazyComponent<typeof import("../components/ui/ConfirmDialog.vue")['default']>
export const LazyUiDataTable: LazyComponent<typeof import("../components/ui/DataTable.vue")['default']>
export const LazyUiDrawer: LazyComponent<typeof import("../components/ui/Drawer.vue")['default']>
export const LazyUiEmptyState: LazyComponent<typeof import("../components/ui/EmptyState.vue")['default']>
export const LazyUiFilterBar: LazyComponent<typeof import("../components/ui/FilterBar.vue")['default']>
export const LazyUiFormField: LazyComponent<typeof import("../components/ui/FormField.vue")['default']>
export const LazyUiIcon: LazyComponent<typeof import("../components/ui/Icon.vue")['default']>
export const LazyUiIconButton: LazyComponent<typeof import("../components/ui/IconButton.vue")['default']>
export const LazyUiInput: LazyComponent<typeof import("../components/ui/Input.vue")['default']>
export const LazyUiKbd: LazyComponent<typeof import("../components/ui/Kbd.vue")['default']>
export const LazyUiModal: LazyComponent<typeof import("../components/ui/Modal.vue")['default']>
export const LazyUiNumberInput: LazyComponent<typeof import("../components/ui/NumberInput.vue")['default']>
export const LazyUiPageHeader: LazyComponent<typeof import("../components/ui/PageHeader.vue")['default']>
export const LazyUiPaginationBar: LazyComponent<typeof import("../components/ui/PaginationBar.vue")['default']>
export const LazyUiSearchField: LazyComponent<typeof import("../components/ui/SearchField.vue")['default']>
export const LazyUiSegmentedControl: LazyComponent<typeof import("../components/ui/SegmentedControl.vue")['default']>
export const LazyUiSelect: LazyComponent<typeof import("../components/ui/Select.vue")['default']>
export const LazyUiSkeleton: LazyComponent<typeof import("../components/ui/Skeleton.vue")['default']>
export const LazyUiStatCard: LazyComponent<typeof import("../components/ui/StatCard.vue")['default']>
export const LazyUiSwitch: LazyComponent<typeof import("../components/ui/Switch.vue")['default']>
export const LazyUiTabs: LazyComponent<typeof import("../components/ui/Tabs.vue")['default']>
export const LazyUiToast: LazyComponent<typeof import("../components/ui/Toast.vue")['default']>
export const LazyUiToastProvider: LazyComponent<typeof import("../components/ui/ToastProvider.vue")['default']>
export const LazyNuxtWelcome: LazyComponent<typeof import("../node_modules/nuxt/dist/app/components/welcome.vue")['default']>
export const LazyNuxtLayout: LazyComponent<typeof import("../node_modules/nuxt/dist/app/components/nuxt-layout")['default']>
export const LazyNuxtErrorBoundary: LazyComponent<typeof import("../node_modules/nuxt/dist/app/components/nuxt-error-boundary.vue")['default']>
export const LazyClientOnly: LazyComponent<typeof import("../node_modules/nuxt/dist/app/components/client-only")['default']>
export const LazyDevOnly: LazyComponent<typeof import("../node_modules/nuxt/dist/app/components/dev-only")['default']>
export const LazyServerPlaceholder: LazyComponent<typeof import("../node_modules/nuxt/dist/app/components/server-placeholder")['default']>
export const LazyNuxtLink: LazyComponent<typeof import("../node_modules/nuxt/dist/app/components/nuxt-link")['default']>
export const LazyNuxtLoadingIndicator: LazyComponent<typeof import("../node_modules/nuxt/dist/app/components/nuxt-loading-indicator")['default']>
export const LazyNuxtTime: LazyComponent<typeof import("../node_modules/nuxt/dist/app/components/nuxt-time.vue")['default']>
export const LazyNuxtRouteAnnouncer: LazyComponent<typeof import("../node_modules/nuxt/dist/app/components/nuxt-route-announcer")['default']>
export const LazyNuxtAnnouncer: LazyComponent<typeof import("../node_modules/nuxt/dist/app/components/nuxt-announcer")['default']>
export const LazyNuxtImg: LazyComponent<typeof import("../node_modules/nuxt/dist/app/components/nuxt-stubs")['NuxtImg']>
export const LazyNuxtPicture: LazyComponent<typeof import("../node_modules/nuxt/dist/app/components/nuxt-stubs")['NuxtPicture']>
export const LazyNuxtPage: LazyComponent<typeof import("../node_modules/nuxt/dist/pages/runtime/page")['default']>
export const LazyNoScript: LazyComponent<typeof import("../node_modules/nuxt/dist/head/runtime/components")['NoScript']>
export const LazyLink: LazyComponent<typeof import("../node_modules/nuxt/dist/head/runtime/components")['Link']>
export const LazyBase: LazyComponent<typeof import("../node_modules/nuxt/dist/head/runtime/components")['Base']>
export const LazyTitle: LazyComponent<typeof import("../node_modules/nuxt/dist/head/runtime/components")['Title']>
export const LazyMeta: LazyComponent<typeof import("../node_modules/nuxt/dist/head/runtime/components")['Meta']>
export const LazyStyle: LazyComponent<typeof import("../node_modules/nuxt/dist/head/runtime/components")['Style']>
export const LazyHead: LazyComponent<typeof import("../node_modules/nuxt/dist/head/runtime/components")['Head']>
export const LazyHtml: LazyComponent<typeof import("../node_modules/nuxt/dist/head/runtime/components")['Html']>
export const LazyBody: LazyComponent<typeof import("../node_modules/nuxt/dist/head/runtime/components")['Body']>
export const LazyNuxtIsland: LazyComponent<typeof import("../node_modules/nuxt/dist/app/components/nuxt-island")['default']>

export const componentNames: string[]
