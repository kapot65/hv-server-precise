<script setup>
import { useSocketStore } from "./stores/socket";
import { Plot } from "@hedger/vue-plotly";
import {
  IonPage,
  IonButton,
  IonContent,
  alertController,
  IonCol,
  IonGrid,
  IonRow,
  IonInput,
  IonList,
  IonItem,
  IonLabel,
} from "@ionic/vue";
import { RecycleScroller } from "vue-virtual-scroller";
import { computed, ref } from "vue";

const socketStore = useSocketStore();

const desiredVoltage = ref(0.0);
const socketOnline = ref(false);

function url(s) {
  let l = window.location;
  return ((l.protocol === "https:") ? "wss://" : "ws://") + l.host + l.pathname + s;
}

// TODO: move into function (reconnect)
let socket = new WebSocket(url("channel"));

socket.onopen = () => {
  if (socket.readyState === 1) {
    socketOnline.value = true;
  }
};

socket.onclose = async () => {
  socketOnline.value = false;
  const alert = await alertController.create({
    header: "WS connection closed",
    message: "Refresh page to reconnect.",
    buttons: ["OK"],
  });
  await alert.present();
};

function setVoltage(voltage) {
  socket.send(
    JSON.stringify({
      type: "command",
      command_type: "set_voltage",
      block: 1,
      voltage,
    })
  );
}

socket.onmessage = ev => {
  let message = JSON.parse(ev.data);
  console.log(message);
  socketStore.putMessage(message);
};

const messagesWithIdx = computed(() =>
  socketStore.messages.map((obj, idx) => ({ idx, ...obj })).reverse()
);

const plotData = computed(() => {
  const getVoltageMessages = socketStore.messages.filter(
    (msg) =>
      msg.message.type === "answer" &&
      msg.message.answer_type === "get_voltage" &&
      msg.message.block === 1
  );

  return [{
      x: getVoltageMessages.map(t => t.time),
      y: getVoltageMessages.map(t => t.message.voltage),
      type: "scatter",
    }]
  }
);

</script>

<template>
  <ion-page>
    <ion-content :fullscreen="true">
      <ion-grid>
        <ion-row>
          <ion-col size="2">
            <h3>
              {{ socketOnline ? "&#128994; (Online)" : "&#128308; (Offline)" }}
            </h3>
          </ion-col>
          <ion-col size="10"></ion-col>
        </ion-row>
        <ion-row>
          <ion-col size="12">
            <Plot
              :data="plotData"
              :layout="{
                autosize: true,
                margin: {
                  l: 60,
                  r: 10,
                  b: 50,
                  t: 10,
                  pad: 4,
                },
              }"
              :config="{}"
              auto-refresh
            />
          </ion-col>
        </ion-row>
        <ion-row>
          <ion-col>
            <h3>
              {{ plotData[0].y.length === 0? '---' : plotData[0].y[[plotData[0].y.length - 1]].toFixed(5) }} V
            </h3>
          </ion-col>
          <ion-col>
            <ion-item>
              <ion-input
                v-model="desiredVoltage"
                type="number"
                inputmode="numeric"
              />
              <ion-button @click="setVoltage(desiredVoltage)">Set</ion-button>
            </ion-item>
          </ion-col>
          <ion-col></ion-col>
        </ion-row>
        <ion-row>
          <ion-col>
            <ion-list>
              <RecycleScroller
                class="scroller"
                :items="messagesWithIdx"
                :item-size="56"
                key-field="idx"
                v-slot="{ item }"
              >
                <ion-item>
                  <ion-label
                    >{{ item.time.toISOString() }}:
                    {{ item.message }}</ion-label
                  >
                </ion-item>
              </RecycleScroller>
            </ion-list>
          </ion-col>
        </ion-row>
    </ion-grid>
    </ion-content>
  </ion-page>
</template>

<style scoped>
.scroller {
  height: 128px;
}

ion-col {
  background-color: #f7f7f7;
  border: solid 1px #ddd;
  padding: 10px;
}

</style>
