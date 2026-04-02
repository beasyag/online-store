<script setup lang="ts">
const props = defineProps<{
  modelValue: string;
  placeholder?: string;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: string];
  submit: [];
}>();

const localValue = ref(props.modelValue);

watch(
  () => props.modelValue,
  (value) => {
    localValue.value = value;
  }
);
</script>

<template>
  <form class="panel relative overflow-hidden p-4 sm:p-5" @submit.prevent="emit('submit')">
    <div class="absolute inset-x-0 top-0 h-20 bg-gradient-to-r from-clay/10 via-transparent to-pine/10" />
    <div class="relative space-y-4">
      <div class="flex flex-col gap-3 sm:flex-row sm:items-center">
        <input
          v-model="localValue"
          type="search"
          class="field h-14 flex-1"
          :placeholder="placeholder || 'Поиск товаров, брендов и категорий...'"
          @input="emit('update:modelValue', localValue)"
        />
        <button class="btn-primary h-14 sm:min-w-[160px]" type="submit">Найти</button>
      </div>
      <div class="flex flex-wrap gap-2 text-sm">
        <span class="badge !bg-white !text-ink">iPhone</span>
        <span class="badge !bg-white !text-ink">LEGO</span>
        <span class="badge !bg-white !text-ink">Dyson</span>
        <span class="badge !bg-white !text-ink">Nike</span>
      </div>
    </div>
  </form>
</template>
