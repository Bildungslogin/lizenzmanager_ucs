/*
 * Copyright 2021 Univention GmbH
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
  '../../common/Page',
  'umc/widgets/Grid',
  'umc/widgets/SearchForm',
  'umc/widgets/Text',
  'umc/widgets/TextBox',
  'put-selector/put',
  'umc/widgets/Form',
  'umc/tools',
  '../../common/ProductColumns',
  'umc/i18n!umc/modules/licenses',
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
    Page,
    Grid,
    SearchForm,
    Text,
    TextBox,
    put,
    Form,
    tools,
    ProductColumns,
    _,
) {
  return declare('umc.modules.licenses.ProductSearchPage', [Page, ProductColumns], {
    //// overwrites
    fullWidth: true,

    //// self
    standbyDuring: null, // required parameter
    moduleFlavor: null, // required parameter
    showChangeSchoolButton: false,

    _grid: null,
    _gridGroup: null,
    _searchForm: null,

    maxUserSum: '-',
    assignedSum: '-',
    expiredSum: '-',
    availableSum: '-',
    userCount: null,

    updateText: function() {
      domClass.remove(this._assignmentText.domNode, 'dijitDisplayNone');
      if (this.getAssignmentType() === 'user') {
        this.removeChild(this._grid);
        this.removeChild(this._gridGroup);
        const count = this.getUserIds().length;
        const id = this.id + '-tooltipNode';
        const msg = `
				<p>
					${entities.encode(
            count === 1
                ? _('Assign licenses to 1 selected user.')
                : _('Assign licenses to %s selected users.', count),
        )}
					<span id="${id}" class="licensesShowSelection">
						(${entities.encode(_('show selected users'))})
					</span>
				</p>
				<p>
					${entities.encode(
            _('Choose the medium for which you want to assign licenses.'),
        )}
				</p>
			`.trim();
        this._assignmentText.set('content', msg);
        const node = dom.byId(id);
        on(
            node,
            'click',
            lang.hitch(this, function(evt) {
              let label = '';
              for (const username of this.getUserIds()) {
                label += `<div>${entities.encode(username)}</div>`;
              }
              Tooltip.show(label, node);
              evt.stopImmediatePropagation();
              on.once(
                  window,
                  'click',
                  lang.hitch(this, function(event) {
                    Tooltip.hide(node);
                  }),
              );
            }),
        );
      } else if (this.getAssignmentType() === 'workgroup' || this.getAssignmentType() === 'schoolClass') {
        this.removeChild(this._grid);
        const id = this.id + '-tooltip';
        const msg = `
				<p>
					${entities.encode(_('Assign licenses to selected workgroup/class.'))}
					<span id="${id}" class="licensesShowSelection">
						(${entities.encode(_('show selected workgroup/class'))})
					</span>
				</p>
				<p>
					${entities.encode(
            _('Choose the medium for which you want to assign licenses.'),
        )}
				</p>
			`.trim();
        this._assignmentText.set('content', msg);
        const node = dom.byId(id);
        on(
            node,
            'click',
            lang.hitch(this, function(evt) {
              let label = '';
              label = `<div>${entities.encode(
                    this.getGroupName(),
                )}</div>`;

              Tooltip.show(label, node);
              evt.stopImmediatePropagation();
              on.once(
                  window,
                  'click',
                  lang.hitch(this, function(event) {
                    Tooltip.hide(node);
                  }),
              );
            }),
        );
      }
    },

    parseGroupName: function(inputValue) {
      return inputValue.split(',')[0].slice(3);
    },

    query: function() {
      this.standbyDuring(
          this._searchForm.ready().then(
              lang.hitch(this, function() {
                this._searchForm.submit();
              }),
          ),
      );
    },

    showUserCount: function() {
      const count = this.userCount;
      const id = this.id + '-tooltipNode';
      const msg = `
				<p>
					${entities.encode(
          count === 1
              ? _('Assign licenses to 1 selected user.')
              : _('Assign licenses to %s selected users.', count),
      )}
					<span id="${id}" class="licensesShowSelection">
						(${entities.encode(_('show selected workgroup/class'))})
					</span>
				</p>
				<p>
					${entities.encode(
          _('Choose the medium for which you want to assign licenses.'),
      )}
				</p>
			`.trim();
      this._assignmentText.set('content', msg);
      const node = dom.byId(id);
      on(
          node,
          'click',
          lang.hitch(this, function(evt) {
            let label = '';

              label = `<div>${entities.encode(
                  this.getGroupName(),
              )}</div>`;

            Tooltip.show(label, node);
            evt.stopImmediatePropagation();
            on.once(
                window,
                'click',
                lang.hitch(this, function(event) {
                  Tooltip.hide(node);
                }),
            );
          }),
      );
    },

    onBack: function() {
      // event stub
    },

    onProductChosen: function() {
      // event stub
    },

    onProductChosenForSchool: function() {
      // event stub
    },

    onProductChosenForClass: function() {
      // event stub
    },

    onProductChosenForWorkgroup: function() {
      // event stub
    },

    onChangeUsers: function() {
      // event stub
    },

    onChooseDifferentSchool: function() {
      // event stub
    },

    onShowProduct: function(productId) {
      // event stub
    },

    exportToExcel: function(values) {
      if (this.getAssignmentType() === 'user') {
        values.licenseType = ['SINGLE', 'VOLUME'];
        values.showOnlyAvailable = true;
      } else if (['workgroup', 'schoolClass'].includes(this.getAssignmentType())) {
        values.groupName = this.parseGroupName(this.getGroup());
        values.licenseType = ['WORKGROUP'];
        values.showOnlyAvailable = true;
      }
      tools.umcpCommand('licenses/products/export_to_excel', values).then(
          lang.hitch(this, function(response) {
            const res = response.result;
            if (res.errorMessage) {
              dialog.alert(result.errorMessage);
            } else {
              downloadFile(res.URL, 'products.xlsx');
            }
            this._excelExportForm._buttons.submit.set('disabled', false);
          }),
      );
    },

    refreshGrid: function(values, resize = false) {
      values.school = this.getSchoolId();
      if (this.getAssignmentType() === 'user') {
        values.licenseType = ['SINGLE', 'VOLUME'];
        values.showOnlyAvailable = true;
        this._grid.filter(values);
        this.removeChild(this._gridGroup);
        this.addChild(this._grid);
        if (resize) {
          this._grid.resize();
        }
      } else if (['workgroup', 'schoolClass'].includes(this.getAssignmentType())) {
        values.groupName = this.parseGroupName(this.getGroup());
        values.licenseType = ['WORKGROUP'];
        values.showOnlyAvailable = true;

        let setUserCount = this.setUserCount;

        this._gridGroup.filter(values).then(() => {

          if (
              this._gridGroup.collection.data[0] &&
              this._gridGroup.collection.data[0].user_count !== null
          ) {
            this._set('userCount',
                this._gridGroup.collection.data[0].user_count);
            this.showUserCount();
            setUserCount(this._gridGroup.collection.data[0].user_count);
          }
        });
        this.removeChild(this._grid);
        this.addChild(this._gridGroup);
        if (resize) {
          this._gridGroup.resize();
        }
      }
    },

    onPageChange: function() {
      this.activeCover.map(function(element) {
        Tooltip.hide(element);
      });
      return true;
    },

    registerCover: function(target) {
      this.activeCover.push(target);
    },

    afterPageChange: function() {
      this.updateText();
      this.refreshGrid({pattern: ''}, true);
    },

    buildRendering: function() {
      this.inherited(arguments);
      this.activeCover = [];

      this._assignmentText = new Text({
        region: 'nav',
        class: 'dijitDisplayNone',
      });


      const widgets = [
        {
          type: TextBox,
          name: 'pattern',
          label: '&nbsp;',
          inlineLabel: _('Search licensed media'),
        },
      ];
      this._searchForm = new SearchForm({
        class: 'umcUDMSearchForm umcUDMSearchFormSimpleTextBox',
        region: 'nav',
        widgets: widgets,
        layout: [['pattern', 'submit']],
        onSearch: lang.hitch(this, function(values) {
          this.refreshGrid(values, true);
        }),
      });

      const actions = [];
      actions.push({
        name: 'edit',
        label: _('To license selection'),
        isStandardAction: true,
        isContextAction: true,
        isMultiAction: false,
        callback: lang.hitch(this, function(_idxs, products) {
          this.setProductId(products[0].productId);
        }),
      });

      this._grid = new Grid({
        actions: actions,
        columns: this.getColumns(),
        moduleStore: store('productId', 'licenses/products'),
        sortIndex: -7,
        addTitleOnCellHoverIfOverflow: true,
      });
      this._gridGroup = new Grid({
        actions: actions,
        columns: this.getColumns(),
        moduleStore: store('productId', 'licenses/products'),
        sortIndex: -7,
        addTitleOnCellHoverIfOverflow: true,
        gridOptions: {
          selectionMode: 'single',
        },
        selectorType: 'radio',
      });

      // FIXME(?) usage of private inherited variables
      aspect.around(
          this._grid._grid,
          'renderRow',
          lang.hitch(this, function(renderRow) {
            return lang.hitch(this, function(item, options) {
              const rowNode = renderRow.call(this._grid._grid, item, options);
              if (item.cover) {
                // .field-title should always exist. just to be safe
                const tooltipTarget =
                    query('.field-title', rowNode)[0] || rowNode;
                this.registerCover(tooltipTarget);
                on(rowNode, mouse.enter, function() {
                  Tooltip.show(_('Loading cover...'), tooltipTarget);
                  let showImage = true;
                  const img = put(
                      document.body,
                      `img.dijitOffScreen.licensesCover[src="${item.cover}"]`,
                  );
                  on(img, 'load', function() {
                    if (showImage) {
                      const innerHTML = `<img src="${item.cover}" style="width: ${img.clientWidth}px; height: ${img.clientHeight}px">`;
                      Tooltip.show(innerHTML, tooltipTarget);
                    }
                  });
                  on(img, 'error', function() {
                    if (showImage) {
                      Tooltip.show(_('Cover not found'), tooltipTarget);
                    }
                  });
                  on.once(rowNode, mouse.leave, function() {
                    showImage = false;
                    Tooltip.hide(tooltipTarget);
                  });
                });
              }
              return rowNode;
            });
          }),
      );

      // FIXME(?) usage of private inherited variables
      aspect.around(
          this._gridGroup,
          'renderRow',
          lang.hitch(this, function(renderRow) {
            return lang.hitch(this, function(item, options) {
              const rowNode = renderRow.call(this._gridGroup, item, options);
              if (item.cover) {
                // .field-title should always exist. just to be safe
                const tooltipTarget =
                    query('.field-title', rowNode)[0] || rowNode;
                on(rowNode, mouse.enter, function() {
                  Tooltip.show(_('Loading cover...'), tooltipTarget);
                  let showImage = true;
                  const img = put(
                      document.body,
                      `img.dijitOffScreen.licensesCover[src="${item.cover}"]`,
                  );
                  on(img, 'load', function() {
                    if (showImage) {
                      const innerHTML = `<img src="${item.cover}" style="width: ${img.clientWidth}px; height: ${img.clientHeight}px">`;
                      Tooltip.show(innerHTML, tooltipTarget);
                    }
                  });
                  on(img, 'error', function() {
                    if (showImage) {
                      Tooltip.show(_('Cover not found'), tooltipTarget);
                    }
                  });
                  on.once(rowNode, mouse.leave, function() {
                    showImage = false;
                    Tooltip.hide(tooltipTarget);
                  });
                });
              }
              return rowNode;
            });
          }),
      );

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
            this._excelExportForm._buttons.submit.set('disabled', true);
            values = this._searchForm.value;
            values.school = this.getSchoolId();
            values.pattern = this._searchForm.value.pattern;
            this.exportToExcel(values);
          }),
      );

      this.addChild(this._assignmentText);
      this.addChild(this._searchForm);
      this.addChild(this._excelExportForm);

    },
  });
});
