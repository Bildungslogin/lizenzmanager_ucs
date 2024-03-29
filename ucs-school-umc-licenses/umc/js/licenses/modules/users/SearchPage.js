/*
 * Copyright 2023 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <http://www.gnu.org/licenses/>.
 */
/*global define*/

define([
  'dojo/_base/declare',
  'dojo/_base/lang',
  'dojo/dom',
  'dojo/dom-class',
  'dojo/aspect',
  'dojo/on',
  'dojo/mouse',
  'dojo/query',
  'dojo/date/locale',
  'dojox/html/entities',
  'dijit/Tooltip',
  'umc/store',
  'umc/tools',
  '../../common/Page',
  'umc/widgets/Grid',
  'umc/widgets/Form',
  'umc/widgets/SearchForm',
  'umc/widgets/TextBox',
  'umc/widgets/DateBox',
  'umc/widgets/ComboBox',
  'umc/widgets/CheckBox',
  'umc/widgets/SuggestionBox',
  'umc/widgets/Text',
  'put-selector/put',
  'dojo/Deferred',
  'umc/widgets/ProgressInfo',
  '../../common/FormatterMixin',
  'umc/i18n!umc/modules/licenses',
  '../../../libraries/FileHelper',
  '../../../libraries/base64',
], function(
    declare,
    lang,
    dom,
    domClass,
    aspect,
    on,
    mouse,
    query,
    dateLocale,
    entities,
    Tooltip,
    store,
    tools,
    Page,
    Grid,
    Form,
    SearchForm,
    TextBox,
    DateBox,
    ComboBox,
    CheckBox,
    SuggestionBox,
    Text,
    put,
    Deferred,
    ProgressInfo,
    FormatterMixin,
    _,
) {
  return declare('umc.modules.licenses.users.SearchPage',
      [Page, FormatterMixin], {
        //// overwrites
        fullWidth: true,

        //// self
        standbyDuring: null, // required parameter
        moduleFlavor: null, // required parameter
        getSchoolId: function() {
        }, // required parameter
        showChangeSchoolButton: false,
        activeCover: [],

        _grid: null,
        _gridGroup: null,
        _excelExportForm: null,
        _searchForm: null,

        maxUserSum: '-',
        assignedSum: '-',
        expiredSum: '-',
        availableSum: '-',
        userCount: null,
        failedAssignments: [],

        query: function() {
          this.standbyDuring(
              this._searchForm.ready().then(
                  lang.hitch(this, function() {
                    this._searchForm.submit();
                  }),
              ),
          );
        },

        afterPageChange: function() {
          if (this._grid) {
            this._grid.resize();
          }
        },

        refreshGrid: function(values, resize = false) {
          values.school = this.getSchoolId();
          this._grid.filter(values);
        },

        exportToExcel: function(values) {
          tools.umcpCommand('licenses/users/export_to_excel', values).then(
              lang.hitch(this, function(response) {
                const res = response.result;
                if (res.errorMessage) {
                  dialog.alert(result.errorMessage);
                } else {
                  downloadFile(res.URL, 'user.xlsx');
                }
                this._excelExportForm._buttons.submit.set('disabled', false);
              }),
          );
        },

        removeLicenseFromUsers: function() {
          if (this.delete_assigments.length > 0) {
            let item = this.delete_assigments.shift();

            tools.umcpCommand('licenses/remove_from_users', {
              licenseCode: item.license,
              usernames: [item.uid],
            }).then(
                lang.hitch(this, function(response) {
                  const failedAssignments = response.result.failedAssignments;
                  if (failedAssignments.length) {
                    this.failedAssignments.concat(failedAssignments);
                  }
                  this.progressInfo.update(Math.floor(
                          100 * this.delete_assigments_count -
                          this.delete_assigments.length /
                          this.delete_assigments_count),
                      _('Licenses are being processed. Please have a little patience.'),
                  );
                  this.removeLicenseFromUsers();
                }),
            );
          } else {
            this.deferred.resolve({
              'error': null,
              'message': null,
              'reason': null,
              'result': null,
            });
            if (this.progressInfo) {
              this.progressInfo.destroyRecursive();
            }
            if (this.failedAssignments.length) {
              const containerWidget = new ContainerWidget({});
              const container = put(containerWidget.domNode, 'div');
              put(
                  container,
                  'p',
                  _('The license could not be removed from the following users:'),
              );
              const table = put(container, 'table');
              for (let failedAssignment of this.failedAssignments) {
                const tr = put(table, 'tr');
                put(tr, 'td', failedAssignment.username);
                put(tr, 'td', failedAssignment.error);
              }
              dialog.alert(containerWidget);
            }
            this._searchForm.submit();
          }
        },

        _toggleSearch: function() {
          this._isAdvancedSearch = !this._isAdvancedSearch;
          [
            'import_date_start',
            'import_date_end',
            'class_group',
            'workgroup',
            'medium',
            'medium_id',
            'publisher',
            'validStatus',
            'usageStatus',
            'notProvisioned'].forEach(lang.hitch(this, function(widgetName) {
            const widget = this._searchForm.getWidget(widgetName);
            if (widget) {
              widget.set('visible', this._isAdvancedSearch);
            }
          }));
        },

        createAfterSchoolChoose: function() {
          this._isAdvancedSearch = false;

          if (this._searchForm) {
            this.removeChild(this._searchForm);
          }

          if (this._excelExportForm) {
            this.removeChild(this._excelExportForm);
          }

          if (this._grid) {
            this.removeChild(this._grid);
          }

          this._excelExportForm = new Form({
            widgets: [],
            buttons: [
              {
                name: 'submit',
                label: _('Export'),
                style: 'margin-top:20px',
              },
            ],
          });

          this._excelExportForm.on(
              'submit',
              lang.hitch(this, function() {
                values = this._searchForm.value;
                values.school = this.getSchoolId();
                values.pattern = this._searchForm.value.pattern;
                this.exportToExcel(values);
              }),
          );

          const widgets = [
            {
              type: DateBox,
              name: 'import_date_start',
              label: _('Import date start'),
              size: 'TwoThirds',
              visible: false
            },
            {
              type: DateBox,
              name: 'import_date_end',
              label: _('Import date end'),
              size: 'TwoThirds',
              visible: false
            },
            {
              type: SuggestionBox,
              name: 'class_group',
              label: _('Class'),
              staticValues: [{id: '', label: ''}],
              dynamicValues: 'licenses/classes',
              dynamicOptions: {
                school: this.getSchoolId(),
              },
              size: 'TwoThirds',
              visible: false
            },
            {
              type: ComboBox,
              name: 'workgroup',
              label: _('Workgroup'),
              size: 'TwoThirds',
              staticValues: [{id: '', label: ''}],
              dynamicValues: 'licenses/workgroups',
              dynamicOptions: {
                school: this.getSchoolId(),
              },
              visible: false
            },
            {
              type: TextBox,
              name: 'username',
              label: _('Username'),
              size: 'TwoThirds',
            },
            {
              type: TextBox,
              name: 'medium',
              label: _('Media Title'),
              size: 'TwoThirds',
              visible: false
            },
            {
              type: TextBox,
              name: 'medium_id',
              label: _('Medium ID'),
              size: 'TwoThirds',
              visible: false
            },
            {
              type: ComboBox,
              name: 'publisher',
              label: _('Publisher'),
              size: 'TwoThirds',
              staticValues: [{id: '', label: ''}],
              dynamicValues: 'licenses/publishers',
              dynamicOptions: {
                school: this.getSchoolId(),
              },
              visible: false
            },
            {
              type: ComboBox,
              name: 'validStatus',
              label: _('Validity status'),
              staticValues: [
                {
                  id: '', label: '',
                },
                {
                  id: '-', label: _('unknown'),
                },
                {
                  id: '0', label: _('invalid'),
                }, {
                  id: '1', label: _('valid'),
                }],
              size: 'TwoThirds',
              visible: false
            },
            {
              type: ComboBox,
              name: 'usageStatus',
              label: _('Usage status'),
              staticValues: [
                {
                  id: '', label: '',
                },
                {
                  id: '-', label: _('unknown'),
                },
                {
                  id: '0', label: _('not activated'),
                }, {
                  id: '1', label: _('activated'),
                }],
              size: 'TwoThirds',
              visible: false
            },
            {
              type: CheckBox,
              name: 'notProvisioned',
              label: _('Only assigned, not yet provisioned licenses'),
              size: 'TwoThirds',
              visible: false
            },
          ];

          const buttons = [
            {
              name: 'toggleSearch', labelConf: {
                class: 'umcFilters',
              }, label: _('Filters'), iconClass: 'umcDoubleRightIcon',

              callback: lang.hitch(this, function() {
                this._toggleSearch();
              }),
            }];

          this._searchForm = new SearchForm({
            class: 'umcUDMSearchForm umcUDMSearchFormSimpleTextBox',
            region: 'nav',
            widgets: widgets,
            buttons: buttons,
            layout: [
              ['import_date_start', 'import_date_end'],
              ['class_group', 'workgroup'],
              ['medium', 'medium_id', 'publisher'],
              ['validStatus', 'usageStatus', 'notProvisioned'],
              ['username', 'submit', 'toggleSearch'],
            ],
            onSearch: lang.hitch(this, function(values) {
              this.refreshGrid(values, true);
            }),
          });

          const actions = [
            {
              name: 'remove',
              label: _('Remove assignment'),
              isStandardAction: true,
              isContextAction: true,
              isMultiAction: true,
              canExecute: function(item) {
                return item.status === 'ASSIGNED';
              },
              callback: lang.hitch(this, function(_idxs, items) {
                this.failedAssignments = [];
                this.deferred = new Deferred();
                this.progressInfo = new ProgressInfo();
                this.delete_assigments = items;
                this.delete_assigments_count = items.length;
                this.progressInfo.update(Math.floor(
                        100 * this.delete_assigments_count -
                        this.delete_assigments.length /
                        this.delete_assigments_count),
                    _('Licenses are being processed. Please have a little patience.'),
                );
                this.standbyDuring(this.deferred, this.progressInfo);
                this.removeLicenseFromUsers();
              }),
            }];

          this._grid = new Grid({
            actions: actions,
            columns: [
              {
                name: 'uid',
                label: _('Username'),
                width: '175px',
              },
              {
                name: 'license',
                label: _('LC'),
                width: '35px',
                formatter: lang.hitch(this, 'formatInvalid')
              },
              {
                name: 'medium',
                label: _('Medium'),
              },
              {
                name: 'classes',
                label: _('Classes'),
                width: '90px',
              },
              {
                name: 'workgroups',
                label: _('Workgroups'),
                width: '90px',
              },
              {
                name: 'roles',
                label: _('Role'),
                width: '20px',
              },
              {
                name: 'publisher',
                label: _('Publisher'),
                width: '35px',
              },
              {
                name: 'date_assignment',
                label: _('Date of assignment'),
                width: '90px',
                formatter: lang.hitch(this, function(value, item) {
                  if (value) {
                    value = dateLocale.format(new Date(value), {
                      fullYear: true, selector: 'date',
                    });
                  }
                  return value;
              }),
              },
              {
                name: 'import_date',
                label: _('Import date'),
                width: '90px',
                formatter: lang.hitch(this, function(value, item) {
                  if (value) {
                    value = dateLocale.format(new Date(value), {
                      fullYear: true, selector: 'date',
                    });
                  }
                  return value;
              }),
              },
            ],
            moduleStore: store('assignment', 'licenses/users/list'),
            sortIndex: -1,
            addTitleOnCellHoverIfOverflow: true,
          });

          this.addChild(this._searchForm);
          this.addChild(this._excelExportForm);
          this.addChild(this._grid);
        },

        buildRendering: function() {
          this.inherited(arguments);
        },
      });
});
