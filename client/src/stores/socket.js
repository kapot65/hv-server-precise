import { ref } from "vue";
import { defineStore } from "pinia";

export const useSocketStore = defineStore("counter", () => {
  const messages = ref([]);

  function putMessage(message) {
    messages.value.push({
      time: new Date(),
      message: message,
    });
  }

  return { messages, putMessage };
});
