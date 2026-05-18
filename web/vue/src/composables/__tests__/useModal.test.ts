import { describe, expect, it } from "vitest";
import { useModal } from "../useModal";

describe("useModal", () => {
  it("initializes with isOpen set to false", () => {
    const { isOpen } = useModal();
    expect(isOpen.value).toBe(false);
  });

  it("open() sets isOpen to true", () => {
    const { isOpen, open } = useModal();

    open();

    expect(isOpen.value).toBe(true);
  });

  it("close() sets isOpen to false", () => {
    const { isOpen, open, close } = useModal();

    open();
    expect(isOpen.value).toBe(true);

    close();

    expect(isOpen.value).toBe(false);
  });

  it("multiple calls to open() keep isOpen true", () => {
    const { isOpen, open } = useModal();

    open();
    open();
    open();

    expect(isOpen.value).toBe(true);
  });

  it("close() on already closed modal keeps isOpen false", () => {
    const { isOpen, close } = useModal();

    close();

    expect(isOpen.value).toBe(false);
  });
});
