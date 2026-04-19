<script setup lang="ts">

import type { ChatRoom, ChatMessage } from "~/types";
import { useApiClient } from "~/composables/useApiClient";
import { useAuthStore } from "~/stores/auth";
import { useFormatters } from "~/composables/useFormatters";

const api = useApiClient();
const auth = useAuthStore();
const route = useRoute();
const router = useRouter();
const { formatDate } = useFormatters();

const rooms = ref<ChatRoom[]>([]);
const activeRoomId = ref<number | null>(null);
const messages = ref<ChatMessage[]>([]);
const messageInput = ref("");
const loading = ref(true);

let ws: WebSocket | null = null;
const messagesContainer = ref<HTMLElement | null>(null);

// Прокрутка чата вниз
const scrollToBottom = async () => {
  await nextTick();
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};

// Загрузка комнат
const loadRooms = async () => {
  if (!auth.loggedIn) return;
  try {
    rooms.value = await api.get<ChatRoom[]>("/chat/rooms/list/");
    
    // Если перешли с ?seller_id=X, пытаемся сразу открыть или создать чат
    const targetSellerId = Number(route.query.seller_id);
    if (targetSellerId) {
      const existing = rooms.value.find(r => r.seller === targetSellerId && r.buyer === auth.user?.id);
      if (existing) {
        selectRoom(existing.id);
      } else {
        // Создаем новую комнату
        const newRoom = await api.post<ChatRoom>("/chat/rooms/", { seller_id: targetSellerId });
        rooms.value.unshift(newRoom);
        selectRoom(newRoom.id);
      }
      // Убираем seller_id из URL, чтобы не создавать заново при обновлении
      router.replace({ query: {} });
    }
  } catch (error) {
    console.error("Failed to load rooms", error);
  } finally {
    loading.value = false;
  }
};

const config = useRuntimeConfig();

// Подключение к WebSocket
const connectWebSocket = (roomId: number) => {
  if (ws) {
    ws.close();
  }
  
  // Определяем базовый URL для WebSocket
  const apiBase = config.public.apiBase as string; // например http://localhost:8000/api
  const wsBase = apiBase.replace("http", "ws").replace("/api", ""); // ws://localhost:8000
  
  const token = auth.accessToken;
  const wsUrl = `${wsBase}/ws/chat/${roomId}/?token=${token}`;
  
  ws = new WebSocket(wsUrl);
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === "history") {
      messages.value = data.messages;
      scrollToBottom();
    } else if (data.type === "message") {
      messages.value.push({
        id: data.id,
        text: data.text,
        author: data.author_id,
        author_display: data.author_display,
        created_at: data.created_at,
        is_read: false
      });
      scrollToBottom();
      
      // Обновляем последнее сообщение в списке комнат
      const roomIndex = rooms.value.findIndex(r => r.id === roomId);
      if (roomIndex !== -1) {
        rooms.value[roomIndex].last_message = { text: data.text, created_at: data.created_at };
        // Поднимаем комнату наверх
        const [moved] = rooms.value.splice(roomIndex, 1);
        rooms.value.unshift(moved);
      }
    }
  };
  
  ws.onclose = () => {
    console.log("WebSocket connection closed");
  };
};

const selectRoom = (roomId: number) => {
  activeRoomId.value = roomId;
  messages.value = []; // очищаем пока грузится
  connectWebSocket(roomId);
  
  // Обнуляем счетчик непрочитанных для этой комнаты
  const room = rooms.value.find(r => r.id === roomId);
  if (room) room.unread_count = 0;
};

const sendMessage = () => {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  if (!messageInput.value.trim()) return;
  
  ws.send(JSON.stringify({ text: messageInput.value }));
  messageInput.value = "";
};

onMounted(async () => {
  await auth.bootstrap();
  loadRooms();
});

onUnmounted(() => {
  if (ws) ws.close();
});
</script>

<template>
  <div class="shell flex h-[80vh] flex-col overflow-hidden">
    <!-- Шапка страницы -->
    <div class="mb-4">
      <h1 class="section-title">Сообщения</h1>
    </div>

    <div v-if="!auth.loggedIn" class="panel p-8 text-center text-sm text-slate-500">
      Пожалуйста, <NuxtLink to="/login" class="text-sky-600 hover:underline">войдите</NuxtLink>, чтобы использовать чат.
    </div>

    <div v-else class="panel flex flex-1 overflow-hidden">
      
      <!-- Боковая панель: список комнат -->
      <aside class="w-full border-r border-slate-100 sm:w-1/3 md:w-1/4 lg:w-1/4 overflow-y-auto" :class="{ 'hidden sm:block': activeRoomId }">
        <div v-if="loading" class="p-5 text-sm text-slate-500">Загрузка...</div>
        <div v-else-if="rooms.length === 0" class="p-5 text-sm text-slate-500">У вас пока нет активных диалогов.</div>
        <ul v-else class="divide-y divide-slate-100">
          <li 
            v-for="room in rooms" 
            :key="room.id"
            @click="selectRoom(room.id)"
            class="cursor-pointer p-4 transition-colors hover:bg-slate-50"
            :class="{ 'bg-slate-50 border-l-4 border-l-sky-500': activeRoomId === room.id }"
          >
            <div class="flex items-start justify-between">
              <p class="font-medium text-ink">{{ room.other_party_name || "Собеседник" }}</p>
              <span v-if="room.last_message" class="text-[10px] text-slate-400 whitespace-nowrap ml-2">
                {{ new Date(room.last_message.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) }}
              </span>
            </div>
            <div class="mt-1 flex items-center justify-between">
              <p class="truncate text-xs text-slate-500">
                {{ room.last_message ? room.last_message.text : "Нет сообщений" }}
              </p>
              <span v-if="room.unread_count > 0" class="ml-2 flex h-5 w-5 items-center justify-center rounded-full bg-rose-500 text-[10px] font-bold text-white">
                {{ room.unread_count }}
              </span>
            </div>
          </li>
        </ul>
      </aside>

      <!-- Основная область чата -->
      <main class="flex flex-1 flex-col bg-slate-50/50" :class="{ 'hidden sm:flex': !activeRoomId }">
        
        <div v-if="!activeRoomId" class="flex h-full items-center justify-center p-8 text-center text-slate-500">
          <p>Выберите диалог слева, чтобы начать общение</p>
        </div>

        <template v-else>
          <!-- Мобильная кнопка назад -->
          <div class="border-b border-slate-100 bg-white p-3 sm:hidden">
            <button @click="activeRoomId = null" class="text-sm font-medium text-sky-600 flex items-center gap-1">
              ← Назад к списку
            </button>
          </div>

          <!-- Окно сообщений -->
          <div ref="messagesContainer" class="flex-1 overflow-y-auto p-4 space-y-4">
            <div class="text-center text-xs text-slate-400 my-4">Начало истории сообщений</div>
            
            <div 
              v-for="msg in messages" 
              :key="msg.id"
              class="flex flex-col max-w-[80%]"
              :class="msg.author === auth.user?.id ? 'self-end items-end' : 'self-start items-start'"
            >
              <span class="text-[10px] text-slate-400 mb-1 px-1">{{ msg.author_display }}</span>
              <div 
                class="rounded-2xl px-4 py-2 text-sm shadow-sm"
                :class="msg.author === auth.user?.id ? 'bg-sky-500 text-white rounded-br-none' : 'bg-white border border-slate-100 text-ink rounded-bl-none'"
              >
                {{ msg.text }}
              </div>
              <span class="text-[10px] text-slate-400 mt-1 px-1">
                {{ new Date(msg.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) }}
              </span>
            </div>
          </div>

          <!-- Поле ввода -->
          <div class="border-t border-slate-100 bg-white p-4">
            <form @submit.prevent="sendMessage" class="flex items-end gap-2">
              <textarea 
                v-model="messageInput"
                @keydown.enter.prevent="sendMessage"
                placeholder="Напишите сообщение..." 
                class="field min-h-[44px] flex-1 resize-none py-3"
                rows="1"
              ></textarea>
              <button 
                type="submit" 
                class="btn-primary flex h-11 w-11 items-center justify-center rounded-full p-0 flex-shrink-0"
                :disabled="!messageInput.trim()"
              >
                ➤
              </button>
            </form>
            <p class="mt-2 text-[10px] text-slate-400 text-center">Нажмите Enter для отправки</p>
          </div>
        </template>
        
      </main>
    </div>
  </div>
</template>
