<script setup lang="ts">
import type { Category, Product, Tag } from "~/types";
import { useFormatters } from "~/composables/useFormatters";

const props = defineProps<{
  categories: Category[];
  tags: Tag[];
  initialValue?: Partial<Product> & {
    category_id?: number;
    tag_ids?: number[];
  };
  submitLabel?: string;
}>();

const emit = defineEmits<{
  submit: [payload: Record<string, unknown>];
}>();
const { formatCategoryName, formatTagName } = useFormatters();

const form = reactive({
  name: "",
  description: "",
  category_id: null as number | null,
  price: "",
  old_price: "",
  image_url: "",
  stock: 10,
  is_active: true,
  tag_ids: [] as number[]
});

const syncForm = () => {
  form.name = props.initialValue?.name || "";
  form.description = props.initialValue?.description || "";
  form.category_id = props.initialValue?.category_id || props.initialValue?.category?.id || props.categories[0]?.id || null;
  form.price = props.initialValue?.price || "";
  form.old_price = props.initialValue?.old_price || "";
  form.image_url = props.initialValue?.image_url || "";
  form.stock = props.initialValue?.stock || 10;
  form.is_active = props.initialValue?.is_active ?? true;
  form.tag_ids = props.initialValue?.tag_ids || props.initialValue?.tags?.map((tag) => tag.id) || [];
};

watch(
  () => [props.initialValue, props.categories],
  () => syncForm(),
  { deep: true, immediate: true }
);
</script>

<template>
  <form class="panel space-y-5 p-6" @submit.prevent="emit('submit', { ...form })">
    <div class="grid gap-5 lg:grid-cols-2">
      <div class="space-y-2 lg:col-span-2">
        <label class="text-sm font-semibold text-ink">Название товара</label>
        <input v-model="form.name" class="field" required />
      </div>

      <div class="space-y-2 lg:col-span-2">
        <label class="text-sm font-semibold text-ink">Описание</label>
        <textarea v-model="form.description" rows="5" class="field" required />
      </div>

      <div class="space-y-2">
        <label class="text-sm font-semibold text-ink">Категория</label>
        <select v-model="form.category_id" class="field" required>
          <option v-for="category in categories" :key="category.id" :value="category.id">
            {{ formatCategoryName(category.name) }}
          </option>
        </select>
      </div>

      <div class="space-y-2">
        <label class="text-sm font-semibold text-ink">Ссылка на изображение</label>
        <input v-model="form.image_url" class="field" type="url" required />
      </div>

      <div class="space-y-2">
        <label class="text-sm font-semibold text-ink">Цена</label>
        <input v-model="form.price" class="field" min="0" step="0.01" type="number" required />
      </div>

      <div class="space-y-2">
        <label class="text-sm font-semibold text-ink">Старая цена</label>
        <input v-model="form.old_price" class="field" min="0" step="0.01" type="number" />
      </div>

      <div class="space-y-2">
        <label class="text-sm font-semibold text-ink">Остаток</label>
        <input v-model="form.stock" class="field" min="0" type="number" required />
      </div>

      <div class="space-y-2">
        <label class="text-sm font-semibold text-ink">Статус</label>
        <select v-model="form.is_active" class="field">
          <option :value="true">Активен</option>
          <option :value="false">Скрыт</option>
        </select>
      </div>

      <div class="space-y-2 lg:col-span-2">
        <label class="text-sm font-semibold text-ink">Теги</label>
        <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <label
            v-for="tag in tags"
            :key="tag.id"
            class="flex items-center gap-3 rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3 text-sm"
          >
            <input v-model="form.tag_ids" type="checkbox" :value="tag.id" />
            <span>{{ formatTagName(tag.name) }}</span>
          </label>
        </div>
      </div>
    </div>

    <button class="btn-primary" type="submit">
      {{ submitLabel || "Сохранить товар" }}
    </button>
  </form>
</template>
