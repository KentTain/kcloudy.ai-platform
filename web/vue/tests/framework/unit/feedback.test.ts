// web/vue/tests/framework/unit/feedback.test.ts
import { beforeEach, describe, expect, it, vi } from "vitest"

// Mock vue-sonner
vi.mock("vue-sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
  },
}))

import { toast } from "vue-sonner"
import {
  confirmAction,
  getErrorMessage,
  notifyBatchError,
  notifyBatchSuccess,
  notifyError,
  notifyInfo,
  notifySuccess,
  notifyWarning,
} from "@/framework/utils/feedback"

describe("feedback utils", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe("notifySuccess", () => {
    it("should call toast.success with message", () => {
      notifySuccess("操作成功")
      expect(toast.success).toHaveBeenCalledWith("操作成功", undefined)
    })

    it("should call toast.success with options", () => {
      notifySuccess("保存成功", { id: "save", duration: 5000 })
      expect(toast.success).toHaveBeenCalledWith("保存成功", { id: "save", duration: 5000 })
    })
  })

  describe("notifyError", () => {
    it("should call toast.error with message", () => {
      notifyError("操作失败")
      expect(toast.error).toHaveBeenCalledWith("操作失败", undefined)
    })

    it("should call toast.error with options", () => {
      notifyError("网络错误", { id: "network", duration: 6000 })
      expect(toast.error).toHaveBeenCalledWith("网络错误", { id: "network", duration: 6000 })
    })
  })

  describe("notifyWarning", () => {
    it("should call toast.warning with message", () => {
      notifyWarning("警告提示")
      expect(toast.warning).toHaveBeenCalledWith("警告提示", undefined)
    })
  })

  describe("notifyInfo", () => {
    it("should call toast.info with message", () => {
      notifyInfo("信息提示")
      expect(toast.info).toHaveBeenCalledWith("信息提示", undefined)
    })
  })

  describe("notifyBatchSuccess", () => {
    it("should show batch success message with count", () => {
      notifyBatchSuccess(10, "删除")
      expect(toast.success).toHaveBeenCalledWith("删除成功", {
        id: "batch-删除",
        description: "已处理 10 项",
      })
    })
  })

  describe("notifyBatchError", () => {
    it("should show batch error message with count", () => {
      notifyBatchError(5, "导入")
      expect(toast.error).toHaveBeenCalledWith("导入失败", {
        id: "batch-导入",
        description: "5 项处理失败",
      })
    })
  })

  describe("confirmAction", () => {
    it("should call window.confirm with message", () => {
      const mockConfirm = vi.spyOn(window, "confirm").mockReturnValue(true)
      const result = confirmAction("确认删除？")
      expect(mockConfirm).toHaveBeenCalledWith("确认删除？")
      expect(result).toBe(true)
      mockConfirm.mockRestore()
    })
  })

  describe("getErrorMessage", () => {
    it("should extract msg from error response", () => {
      const error = {
        response: {
          data: {
            msg: "操作失败",
          },
        },
      }
      expect(getErrorMessage(error, "默认消息")).toBe("操作失败")
    })

    it("should extract detail from error response", () => {
      const error = {
        response: {
          data: {
            detail: "详细信息",
          },
        },
      }
      expect(getErrorMessage(error, "默认消息")).toBe("详细信息")
    })

    it("should return fallback when no response data", () => {
      const error = new Error("网络错误")
      expect(getErrorMessage(error, "默认消息")).toBe("网络错误")
    })

    it("should return fallback for unknown error", () => {
      expect(getErrorMessage("unknown", "默认消息")).toBe("默认消息")
    })
  })
})
