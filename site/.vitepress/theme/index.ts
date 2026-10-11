import DefaultTheme from 'vitepress/theme'
import ProjectHome from './ProjectHome.vue'
import './style.css'

export default {
  extends: DefaultTheme,
  enhanceApp({ app }) {
    app.component('ProjectHome', ProjectHome)
  },
}
