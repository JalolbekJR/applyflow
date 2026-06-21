import { isProxy, toRaw } from 'vue'

export const cloneData = <T>(value: T): T => structuredClone(isProxy(value) ? toRaw(value) : value)
