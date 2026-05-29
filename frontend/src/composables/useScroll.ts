import { ref, onMounted, onUnmounted } from 'vue';

interface ScrollOptions {
  threshold?: number
  throttleDelay?: number
}

type ThrottledFn = ((...args: unknown[]) => void) & { cancel: () => void }

function throttle(fn: (...args: unknown[]) => void, delay: number): ThrottledFn {
  let timerId: ReturnType<typeof setTimeout> | null = null;
  const throttledFn = function (this: unknown, ...args: unknown[]) {
    if (timerId) return;
    timerId = setTimeout(() => {
      fn.apply(this, args);
      timerId = null;
    }, delay);
  } as ThrottledFn;
  throttledFn.cancel = () => {
    if (timerId) {
      clearTimeout(timerId);
    }
  };
  return throttledFn;
}

export function useScroll(options: ScrollOptions = {}) {
  const { threshold = 200, throttleDelay = 100 } = options;
  const showScrollToTop = ref(false);
  const showScrollToBottom = ref(false);
  const handleScroll = () => {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const { scrollHeight, clientHeight } = document.documentElement;
    showScrollToTop.value = scrollTop > threshold;
    showScrollToBottom.value = scrollTop < scrollHeight - clientHeight - threshold;
  };
  const throttledHandleScroll = throttle(handleScroll, throttleDelay);
  onMounted(() => {
    window.addEventListener('scroll', throttledHandleScroll, { passive: true });
    handleScroll();
  });
  onUnmounted(() => {
    window.removeEventListener('scroll', throttledHandleScroll);
    throttledHandleScroll.cancel();
  });
  return { showScrollToTop, showScrollToBottom };
}
