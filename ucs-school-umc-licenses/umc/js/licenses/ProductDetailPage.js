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
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/topic",
	"dojo/store/Memory",
	"dojo/store/Observable",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin",
	"dojox/html/entities",
	"umc/tools",
	"umc/widgets/Page",
	"umc/widgets/Grid",
	"put-selector/put",
	"umc/i18n!umc/modules/licenses"
], function(declare, lang, topic, Memory, Observable, _WidgetBase, _TemplatedMixin, entities, tools, Page, Grid, put, _) {

	const _Table = declare("umc.modules.licenses.Table", [_WidgetBase, _TemplatedMixin], {
		//// overwrites
		templateString: `
			<div class="licensesTable">
				<div
					class="licensesTable__coverWrapper"
				>
					<img
						data-dojo-attach-point="_coverNode"
						class="licensesTable__cover"
					>
				</div>
				<div
					data-dojo-attach-point="_tableNode"
					class="licensesTable__data"
				></div>
			</div>
		`,


		//// self
		standbyDuring: null, // required

		product: null,
		_setProductAttr: function(product) {
			this._coverNode.src = product.cover;
			this._tableNode.innerHTML = '';

			function e(id) {
				let val = product[id];
				if (typeof val === 'string') {
					val = entities.encode(val);
				}
				return val;
			}

			const data = [
				[_('Publisher'),  e('publisher'),   _('Platform'), e('platform')],
				[_('Product ID'), e('productId'),   '',            ''],
				[_('Title'),      e('productName'), '',            ''],
				[_('Author'),     e('author'),      '',            ''],
			];

			for (const row of data) {
				put(this._tableNode,
					'div.licensesTable__dataLabel', row[0],
					'+ div', row[1],
					'+ div.licensesTable__dataLabel', row[2],
					'+ div', row[3]
				);
			}
			this._set('product', product);
		},
	});

	return declare("umc.modules.licenses.ProductDetailPage", [ Page ], {
		//// overwrites
		fullWidth: true,


		//// self
		schoolId: null, // required parameter

		_table: null,
		_grid: null,

		product: null,
		_setProductAttr: function(product) {
			this._table.set('product', product);
			this._grid.moduleStore.setData(product.licenses);
			this._grid.filter();
			this._set('product', product);
		},

		load: function(productId) {
			return this.standbyDuring(
				tools.umcpCommand('licenses/products/get', {
					productId: productId,
				}).then(lang.hitch(this, function(response) {
					const product = response.result;
					this.set('product', product);
					return;
				}))
			);
		},

		onBack: function() {
			// event stub
		},


		//// lifecycle
		postMixInProperties: function() {
			this.headerButtons = [{
				name: 'close',
				label: _('Back'),
				callback: lang.hitch(this, 'onBack'),
			}];
		},

		buildRendering: function() {
			this.inherited(arguments);

			this._table = new _Table({});

			const actions = [{
				name: 'edit',
				label: _('Open license'),
				isStandardAction: true,
				isContextAction: true,
				isMultiAction: false,
				callback: lang.hitch(this, function(idxs, licenses) {
					topic.publish('/umc/modules/open', 'licenses', 'licenses/licenses', {
						moduleState: `school:${this.schoolId}:license:${licenses[0].licenseCode}`,
					});
				}),
			}];
			const columns = [{
				name: 'licenseCode',
				label: _('License code'),
			}, {
				name: 'licenseType',
				label: _('License type'),
			}, {
				name: 'validityStart',
				label: _('Gültigkeitsbeginn'),
			}, {
				name: 'validityEnd',
				label: _('Gültigkeitsende'),
			}, {
				name: 'validitySpan',
				label: _('Gültigkeitsdauer'),
				width: '100px',
			}, {
				name: 'ignore',
				label: _('Ignore'),
				width: '65px',
			}, {
				name: 'countAquired',
				label: _('Aquired'),
				width: '60px',
			}, {
				name: 'countAssigned',
				label: _('Assigned'),
				width: '60px',
			}, {
				name: 'countExpired',
				label: _('Expired'),
				width: '60px',
			}, {
				name: 'countAvailable',
				label: _('Available'),
				width: '60px',
			}, {
				name: 'importDate',
				label: _('Delivery'),
			}];
			this._grid = new Grid({
				actions: actions,
				columns: columns,
				moduleStore: new Observable(new Memory({
					data: [],
					idProperty: 'dn'
				})),
			});

			this.addChild(this._table);
			this.addChild(this._grid);
		},
	});
});

