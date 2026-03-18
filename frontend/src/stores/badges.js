import { defineStore } from 'pinia'
import { badgesAPI } from '../api'

export const useBadgesStore = defineStore('badges', {
  state: () => ({
    badges: [],
    allDefinitions: {
      time: { name: '时间里程碑', badges: [] },
      streak: { name: '签到连续', badges: [] },
      special: { name: '特殊成就', badges: [] }
    }
  }),

  getters: {
    earnedBadges: (state) => state.badges.filter(b => b.earned),
    earnedCount: (state) => state.badges.filter(b => b.earned).length,
    totalCount: (state) => state.badges.length
  },

  actions: {
    async fetchBadges() {
      try {
        const response = await badgesAPI.getList()
        this.badges = response.data.badges || []
      } catch (error) {
        console.error('Fetch badges error:', error)
      }
    },

    async fetchAllDefinitions() {
      try {
        const response = await badgesAPI.getDefinitions()
        this.allDefinitions = response.data.categories || {}
      } catch (error) {
        console.error('Fetch definitions error:', error)
      }
    },

    addNewBadge(badge) {
      this.badges.push(badge)
    }
  }
})
