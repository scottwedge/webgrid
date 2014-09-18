
var datagrid_active_filters = [];
var _datagrid_is_loaded = false;

$(document).ready(function() {
    // sorting
    datagrid_toggle_sort_selects();
    $('.datagrid .header .sorting select').change(datagrid_toggle_sort_selects);

    // filtering
    datagrid_prep_filters();
    $('.datagrid .filters .operator select').change(datagrid_on_operator_change);
    $('.datagrid .filters .add-filter select').change(datagrid_add_filter);
    $('.datagrid .filters .toggle-button').click(datagrid_toggle_mselect);

    $('.inputs1 select').change(function() {
        $(this).siblings('input').val($(this).val());
    });
    _datagrid_is_loaded = true;
});

/*
 datagrid_toggle_mselect()

 Called when the select box in an inputs1 column needs to be turned into a
 multi-select UI element or a multi-select UI element needs to be turned into
 a normal select box.

 MUST be called from a context where "this" refers to the toggle image next to
 the select element.

*/
function datagrid_toggle_mselect(){
    jq_img = $(this);
    jq_select = jq_img.siblings('select');
    select_name = jq_select.attr('name');
    multiple_attr = jq_select.attr('multiple')
    if (typeof multiple_attr !== 'undefined' && multiple_attr !== false) {
        jq_select.removeAttr('multiple');
        jq_select.siblings('.ms-parent').hide();
        jq_select.show();
    } else {
        datagrid_activate_mselect_ui(jq_select);
    }
}

/*
 datagrid_activate_mselect_ui()

 Called to activate the multi-select ui on a select element.

*/
function datagrid_activate_mselect_ui(jq_select) {
    var all_opt = $(jq_select).find('option[value="-1"]');
    var use_all_opt = (all_opt.text() == '-- All --');
    if ( use_all_opt ) {
        $(all_opt).detach();
    }
    if (jq_select.siblings('.ms-parent').length > 0) {
        jq_select.hide();
        jq_select.siblings('.ms-parent').show();
    } else {
        jq_select.multipleSelect({
            onOpen: function() {
                $('.ms-drop input').show();
            },
            minumimCountSelected: 2,
            filter: true
        });
        jq_select.parent().find('.ms-parent > button, .ms-drop').each(function() {
            $(this).css('width', $(this).width() + 60);
        });
    }
    jq_select.attr('multiple', 'multiple');
    if ( use_all_opt ) {
        $(all_opt).prependTo(jq_select);
    }
}

/*
 datagrid_add_filter()

 Called when the Add Filter select box is changed. Shows the operator and input
 fields that corresponds to the filter selected.

*/
function datagrid_add_filter() {
    jq_afs = $('.datagrid .filters .add-filter select');
    filter_key = jq_afs.val();
    if( filter_key != '') {
        datagrid_activate_filter(filter_key);
        jq_afs.val('');
    }
}


/*
 datagrid_prep_filters()

 Called when the page is loaded, this function loops through the filter controls
 table looking for filters that should be active (because of their initial
 operator and input values) and shows the filter's input fields.

*/
function datagrid_prep_filters(){
    $('.datagrid .filters tr').each(function(){
        jq_tr = $(this);
        filter_key = jq_tr.attr('class');
        if( filter_key != 'add-filter') {
            op_select = jq_tr.find('.operator select');
            if( op_select.val() != '' ) {
                // filter should be active, so activate it
                datagrid_activate_filter(filter_key);
            } else {
                // the filter is not active, hide the row
                jq_tr.hide();
            }
            datagrid_toggle_filter_inputs(jq_tr);
        }
    });
}

/*
 datagrid_activate_filter()

 Called initially when the page is loaded and also when the "Add Filter" select
 box is changed to show the row and controls for the given filter key.

*/
function datagrid_activate_filter(filter_key) {
    jq_tr = $('.datagrid .filters tr.' + filter_key);
    // show the filter's row of controls
    jq_tr.show();

    // make sure the option in the "Add Filter" select box for this
    // filter is disabled
    jq_option = $('.datagrid .filters .add-filter option[value="'+filter_key+'"]');
    jq_option.attr('disabled', 'disabled');
}

/*
 datagrid_on_operator_change()

 Called when an operator select box is changed, it calls
 datagrid_toggle_filter_inputs() for the filter in question so that the input
 fields for the filter can be displayed properly.

*/
function datagrid_on_operator_change() {
    jq_op_select = $(this);
    jq_tr = jq_op_select.closest('tr');
    filter_key = jq_tr.attr('class');
    datagrid_toggle_filter_inputs(jq_tr);
}

/*
 datagrid_toggle_filter_inputs()

 Handles showing or hiding the input fields (input/select/multi-select UI) for a
 given filter row.

*/
function datagrid_toggle_filter_inputs(jq_filter_tr) {
    op_key = jq_filter_tr.find('.operator select').val();
    fields1 =  jq_filter_tr.find('.inputs1').children();
    fields2 = jq_filter_tr.find('.inputs2').children();
    v1name = 'v1('+filter_key+')';

    if( op_key == '') {
        // destroy any multi-selects that have been created
        fields1.removeAttr('multiple');
        fields1.siblings('.ms-parent').hide();
        fields1.hide();
        fields1.val('');

        fields2.hide();
        fields2.val('');
    } else {
        op_data = datagrid_data[filter_key][op_key];
        field_type = op_data.field_type;
        if( field_type == null ) {
            fields1.hide();
            fields1.val('');
        } else {
            fields1.show();
            // turn on multi-select for a select field that has multiple
            // set.  The selector is for the toggle-button img, so that
            // datagrid_toggle_mselect() works correctly.
            fields1.siblings('.ms-parent').hide();
            jq_filter_tr.find('.inputs1 select[multiple]').each(function(){
                datagrid_activate_mselect_ui($(this));
            });
            if ( field_type.substring(0,6) == 'select' ) {
                jq_filter_tr.find('.inputs1 input').hide();
                jq_filter_tr.find('.inputs1 select:not([multiple])').show();
                jq_filter_tr.find('.inputs1 input').val(
                    jq_filter_tr.find('.inputs1 select').val()
                );
                if ( field_type == 'select+input' ) {
                    jq_filter_tr.find('.inputs1 .toggle-button').hide();
                    jq_filter_tr.find('.inputs1 input').removeAttr('name');
                    jq_filter_tr.find('.inputs1 select').attr('name',v1name);
                }
            } else {
                if (_datagrid_is_loaded) {
                    jq_filter_tr.find('.inputs1 input').val('');
                }
                jq_filter_tr.find('.inputs1 input').show();
                jq_filter_tr.find('.inputs1 select').hide();
                jq_filter_tr.find('.inputs1 .toggle-button').hide();
                jq_filter_tr.find('.inputs1 input').attr('name',v1name);
                jq_filter_tr.find('.inputs1 select').removeAttr('name');
            }
        }
        if( field_type == '2inputs' || field_type == 'select+input' ) {
            fields2.show();
        } else {
            fields2.hide();
            fields2.val('');
        }
    }
}

/*
 datagrid_filter_inactive() DON'T THINK I NEED THIS ANYMORE

 Utility function that returns a bool value indicating if the filter key passed
 in represents a filter that is currently inactive (and therefore hidden).

*/
function datagrid_filter_inactive(filter_key){
    return $.inArray(filter_key, datagrid_active_filters) == -1;
}

/*
 datagrid_toggle_sort_selects()

 Called when any of the sorting related select boxes change, it handles hiding
 and showing the select boxes.

*/
function datagrid_toggle_sort_selects() {
    jq_dds = $('.datagrid .header .sorting dd');
    if (jq_dds.length == 0) return;
    dd1 = jq_dds.eq(0)
    dd2 = jq_dds.eq(1)
    dd3 = jq_dds.eq(2)
    sb1 = dd1.find('select');
    sb2 = dd2.find('select');
    sb3 = dd3.find('select');

    if( sb1.val() == '' ) {
        dd2.hide();
        sb2.val('');
        dd3.hide();
        sb3.val('');
    } else {
        dd2.show();
        if( sb2.val() == '' ) {
            dd3.hide();
            sb3.val('');
        } else {
            dd3.show();
        }
    }

    $('dl.sorting select option').removeAttr('disabled');
    disable_sort(sb3);
    disable_sort(sb2);
    disable_sort(sb1);
}

/*
 disable_sort()

 Takes the target_id select box and grays out options that have been chosen in sb1 and sb2.

*/
function disable_sort(sb) {
    if ($(sb).val() == '') return;
    var sbval = $(sb).val().replace(/^-/, "");
    $('dl.sorting select[id!="'+$(sb).attr('id')+'"]').find(
        'option[value="'+sbval+'"], option[value="-'+sbval+'"]'
    ).attr('disabled', 'disabled');
}
