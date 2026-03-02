import { create } from 'zustand'

type AppView = 'dashboard' | 'case-review' | 'playbooks'

interface UiState {
  activeView: AppView
  selectedCaseId: string | null
  caseRunLimit: number
  setActiveView: (value: AppView) => void
  setSelectedCaseId: (value: string | null) => void
}

export const useUiStore = create<UiState>((set) => ({
  activeView: 'dashboard',
  selectedCaseId: null,
  caseRunLimit: 20,
  setActiveView: (value) => set({ activeView: value }),
  setSelectedCaseId: (value) => set({ selectedCaseId: value }),
}))
