import { create } from "zustand";

interface OverlayData {
  x: number;
  y: number;
  width: number;
  height: number;
  instruction: string;
}

type Status = "idle" | "processing" | "tracking" | "showingResult" | "done";

interface AssistantState {
  task: string;
  currentStep: number;
  totalSteps: number;
  overlayData: OverlayData | null;
  status: Status;

  setTask: (task: string) => void;
  setOverlayData: (data: OverlayData | null) => void;
  setStatus: (status: Status) => void;
  setStepIndex: (step: number) => void;
  setTotalSteps: (total: number) => void;
  nextStep: () => void;
  reset: () => void;
}

export const useAssistantStore = create<AssistantState>((set) => ({
  task: "",
  currentStep: 0,
  totalSteps: 0,
  overlayData: null,
  status: "idle",

  setTask: (task) => set({ task }),
  setOverlayData: (data) =>
    set({ overlayData: data, status: data ? "showingResult" : "idle" }),
  setStatus: (status) => set({ status }),
  setStepIndex: (step) => set({ currentStep: step }),
  setTotalSteps: (total) => set({ totalSteps: total }),
  nextStep: () =>
    set((state) => {
      const next = state.currentStep + 1;
      return {
        currentStep: next,
        status: next >= state.totalSteps ? "done" : "idle",
      };
    }),
  reset: () =>
    set({
      task: "",
      currentStep: 0,
      totalSteps: 0,
      overlayData: null,
      status: "idle",
    }),
}));
