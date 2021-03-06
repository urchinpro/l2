<template>
  <div ref="root">
    <div id="cont_left" class="split split-horizontal">
      <div id="left_top" class="split content" style="padding: 0;">
        <patient-picker v-model="selected_card" directive_from_need="true" search_results="true" bottom_picker="true">
          <div slot="for_card" class="text-right">
            <div v-if="selected_researches.length > 0"
                 style="margin-top: 5px;text-align: left">
              <table class="table table-bordered lastresults">
                <colgroup>
                  <col width="180">
                  <col>
                  <col width="110">
                  <col width="110">
                </colgroup>
                  <tbody>
                  <last-result :individual="selected_card.individual_pk" v-for="p in selected_researches" :key="p"
                               :research="p"/>
                  </tbody>
                </table>
            </div>
          </div>
          <div slot="for_card_bottom" class="bottom-inner" v-if="selected_card.pk >= 0">
            <!--<a href="#" @click.prevent="do_show_rmis_send_directions" v-if="selected_card.is_rmis">
              <span>Направить в другую МО</span>
            </a>-->
            <a href="#" @click.prevent="do_show_rmis_directions" v-if="selected_card.is_rmis">
              <span>Направления из РМИС</span>
            </a>
            <a :href="report_url">
              <span>Отчёт по результатам</span>
            </a>
            <a v-if="can_create_tickets" :href="ticket_url">
              <span>Создать статталон</span>
            </a>
          </div>
        </patient-picker>
      </div>
      <div id="left_bottom" class="split content" style="padding: 0;">
        <researches-picker v-model="selected_researches"/>
      </div>
    </div>
    <div id="cont_right" class="split split-horizontal">
      <div id="right_top" class="split content" style="padding: 0;">
        <directions-history :patient_pk="selected_card.pk"/>
      </div>
      <div id="right_bottom" class="split content" style="padding: 0;">
        <selected-researches :operator="selected_card.operator" :ofname="selected_card.ofname" :main_diagnosis="selected_card.main_diagnosis"
                             :history_num="selected_card.history_num" :valid="patient_valid"
                             :researches="selected_researches" :base="selected_card.base" :card_pk="selected_card.pk"/>
      </div>
    </div>
    <results-viewer :pk="show_results_pk" v-if="show_results_pk > -1"/>
    <rmis-directions-viewer v-if="show_rmis_directions && selected_card.is_rmis" :card="selected_card"/>
    <!--<rmis-send-directions v-if="show_rmis_send_directions && selected_card.is_rmis" :card="selected_card"/>-->
  </div>
</template>

<script>
  import ResearchesPicker from './ResearchesPicker'
  import PatientPicker from './PatientPicker'
  import SelectedResearches from './SelectedResearches'
  import DirectionsHistory from './DirectionsHistory'
  import ResultsViewer from './ResultsViewer'
  import RmisDirectionsViewer from './RmisDirectionsViewer'
  // import RmisSendDirections from './RmisSendDirections'
  import LastResult from './LastResult'

  export default {
    components: {
      PatientPicker,
      ResearchesPicker,
      SelectedResearches,
      DirectionsHistory,
      ResultsViewer,
      RmisDirectionsViewer,
      // RmisSendDirections,
      LastResult,
    },
    name: 'directions',
    data() {
      return {
        selected_card: {
          pk: -1,
          base: {},
          ofname: -1,
          ofname_dep: -1,
          individual_pk: -1,
          operator: false,
          is_rmis: false,
          history_num: '',
          family: '',
          name: '',
          twoname: '',
          birthday: '',
          age: '',
          main_diagnosis: '',
        },
        selected_researches: [],
        show_results_pk: -1,
        show_rmis_directions: false,
        show_rmis_send_directions: false,
        diagnos: '',
        fin: -1,
      }
    },
    created() {
      let vm = this

      this.$root.$on('show_results', (pk) => {
        vm.show_results_pk = pk
      })

      this.$root.$on('hide_results', () => {
        vm.show_results_pk = -1
      })

      this.$root.$on('hide_rmis_directions', () => {
        vm.show_rmis_directions = false
        vm.show_rmis_send_directions = false
      })

      this.$root.$on('update_diagnos', (diagnos) => {
        vm.diagnos = diagnos
      })

      this.$root.$on('update_fin', (fin) => {
        vm.fin = fin
      })
    },
    mounted() {
      let vm = this
      $(document).ready(function () {
        vm.resize()
        $(window).resize(function () {
          vm.resize()
        })
        Split(['#cont_left', '#cont_right'], {
          gutterSize: 5,
          cursor: 'col-resize',
          minSize: 200,
          onDrag: vm.resize
        })

        Split(['#left_top', '#left_bottom'], {
          direction: 'vertical',
          gutterSize: 5,
          cursor: 'row-resize',
          minSize: 200,
          onDrag: vm.resize
        })

        Split(['#right_top', '#right_bottom'], {
          direction: 'vertical',
          gutterSize: 5,
          cursor: 'row-resize',
          minSize: 200,
          onDrag: vm.resize
        })
      })
      $(window).on('beforeunload', function () {
        if (vm.selected_card.pk === -1 || vm.selected_researches.length <= 0 || document.activeElement && document.activeElement.href && document.activeElement.href.startsWith('sip:')) {
          if (document.activeElement) {
            $(document.activeElement).blur()
          }
        }
        else {
          return 'Исследования выбраны, но направления не созданы. Вы уверены, что хотите покинуть страницу?'
        }
      })
    },
    methods: {
      resize() {
        const $fp = $(this.$refs.root)
        $fp.height($(window).height() - $fp.position().top - 5)
      },
      do_show_rmis_directions() {
        this.show_rmis_directions = true
      },
      do_show_rmis_send_directions() {
        this.show_rmis_send_directions = true
      }
    },
    computed: {
      patient_valid() {
        return this.selected_card.pk !== -1
      },
      ticket_url() {
        return `/mainmenu/statistics-tickets?base_pk=${this.selected_card.base.pk}&card_pk=${this.selected_card.pk}&ofname=${this.selected_card.ofname}&ofname_dep=${this.selected_card.ofname_dep}`
      },
      report_url() {
        return `/mainmenu/results_report?individual_pk=${this.selected_card.individual_pk}&base_pk=${this.selected_card.base.pk}&card_pk=${this.selected_card.pk}`
      },
      can_create_tickets() {
        if ('groups' in this.$store.getters.user_data) {
          for (let g of this.$store.getters.user_data.groups) {
            if (g === 'Оформление статталонов' || g === 'Лечащий врач' || g === 'Оператор лечащего врача') {
              return true
            }
          }
        }
        return false
      },
      step() {
        if(this.patient_valid) {
          if(this.selected_researches.length > 0) {
            if(this.diagnos !== '') {
              if (this.fin === -1) {
                return 3
              }
              return 4
            }
            return 2
          }
          return 1
        }
        return 0
      }
    },
    watch: {
      step() {
        this.$root.$emit('set-step', this.step)
      }
    }
  }
</script>

<style scoped lang="scss">
  #right_top {
    overflow: visible !important;
  }

  .lastresults {
    table-layout: fixed;
    padding: 0;
    margin: 0;
    color: #000;
    background-color: #ffdb4d;
    border-color: #000;
    /deep/ th, /deep/ td {
      border-color: #000;
    }

    /deep/ a {
      color: #000;
      text-decoration: dotted underline;
    }
    /deep/ a:hover {
      text-decoration: none;
    }
  }

  .fli {
    text-decoration: underline;
    margin-left: 5px;
  }

  .fli:hover {
    text-decoration: none;
  }
</style>
