var xingQuestion = {
    subject_id:2,
    report_id:null,
    type:null,
    type_param:null,
    knows_mode:1,
    report_time_long:0,
    user_answer_count:0,
    laytpl:null,
    timer_id:null,
    save_timer:null,
    submiting:false,
    now_timestamp:null,
    header:null,
    last_select_aswer_time:0,
    //加载
    load:function(type,type_param) {
        let _this = this;
        _this.type = type;
        _this.type_param = type_param;
        layui.use('layer', function() {
            var layer = layui.layer;
            layer.load(1,{ shade: [0.3,'#000']});

            $.post('/pc/xingQuestion/begin/subject_id/'+subject_id,{type:type,type_param:type_param},function(resule){
                layer.closeAll();
                if(resule.status==1){
                    _this.header = resule.data.header;
                    _this.report_id = _this.header.report_id;
                    if(resule.data.header.report_method==1 || resule.data.header.report_method==2){
                        _this.knows_mode = resule.data.header.report_method;
                    }

                    _this.now_timestamp = _this.header.now_time;

                    layui.use(['layer','laytpl'], function(){
                        _this.laytpl = layui.laytpl;
                        $('body').data('vip_status',resule.data.header.vip_status);
                        $('body').data('free_xing_video_num',resule.data.header.free_xing_video_num);

                        if(resule.data.ques_data!=undefined){
                            _this.data2View(resule.data.header,resule.data.ques_data,1);
                        }else{
                            _this.data2View(resule.data.header,resule.data.paper_data,2);
                        }


                        //重写报告名称
                        if(_this.type==8){
                            $("#report_name").html(_this.header.report_name + "<span class='report_name-tip'>考试时长："+(_this.header.paper_take_time/60)+"分钟，过时自动交卷</span>");
                        }else if(_this.type==5){
                            let start_str = _this.timestampToTime(_this.header.begin_time);
                            let end_str = _this.timestampToTime(_this.header.end_time);
                            let tmp = _this.header.end_time - _this.header.submit_time;
                            if(tmp>60){
                                tmp =parseInt(tmp/60)+'分钟';
                            }else{
                                tmp = tmp+'秒';
                            }
                            $("#report_name").html(_this.header.report_name + "<span class='report_name-tip'>考试时间："+start_str+" ~ "+end_str+"，可以提前"+tmp+"交卷，考试结束时系统自动交卷</span>");
                        } else{
                            $("#report_name").html(_this.header.report_name);
                        }


                        //判断大模考是否开始
                        if(_this.type == 5){
                            if(_this.now_timestamp < _this.header.begin_time){
                                $(".ques-console-button a").attr('href','javascript:void();').css('width','220px').html('距开考时间还有<span id="mokao_start_tip"></span>');
                                $(".ques-item-answer-item").addClass('disabled');
                            }else{
                                $(".ques-console-button").hide();
                                _this.report_time_long = (_this.header.end_time - _this.header.begin_time) - (_this.header.end_time-_this.now_timestamp);
                                _this.start();
                            }
                        }else{
                            _this.start();
                        }
                        setInterval(function () {
                            _this.now_timestamp++;
                            if(_this.type == 5){
                                if(_this.now_timestamp<_this.header.begin_time){
                                    let tmp = _this.header.begin_time - _this.now_timestamp;
                                    if(tmp>60){
                                        tmp =parseInt(tmp/60)+'分钟';
                                    }else{
                                        tmp = tmp+'秒';
                                    }
                                    $("#mokao_start_tip").text(tmp);
                                }else if($("#mokao_start_tip").length>0){
                                    window.location.reload();
                                }
                            }
                        },1000);

                        //学习记录启动
                        studyTime.subject_id = _this.subject_id;
                        studyTime.addXingQuestion(_this.report_id,0);

                        if(_this.header.message!=null){
                            layer.msg(_this.header.message,{time:5000});
                        }
                    });
                }else{
                    layui.use('layer', function() {
                        var layer = layui.layer;
                        layer.alert(resule.info, {
                            time: 5*1000,
                            success: function(layero, index){
                                var timeNum = this.time/1000, setText = function(start){
                                    layer.title('<span class="layui-font-red">'+ (start ? timeNum : --timeNum) + '</span> 秒后自动返回上一页', index);
                                };
                                setText(!0);
                                this.timer = setInterval(setText, 1000);
                                if(timeNum <= 0){
                                    clearInterval(this.timer);
                                    window.history.back();
                                }
                            },
                            end: function(){
                                clearInterval(this.timer);
                                window.history.back();
                            }
                        });
                    });

                }
            },'json');
        })
    },
    //开始作答
    start:function() {
        let _this = this;
        if(_this.timer_id==null){
            _this.timer_id = setInterval(function () {
                _this.report_time_long++;
                _this.save_timer++;
                $('.ques-console-time').text(_this.getTime(_this.report_time_long));

                //自动交卷
                if(_this.type == 8 && _this.submiting==false){
                    if(_this.report_time_long>=_this.header.paper_take_time){
                        layer.msg('考试结束，自动交卷...', {
                            offset: 't'
                        });
                        _this.submit(1);
                    }
                }else if(_this.type == 5 && _this.submiting==false){
                    if(_this.now_timestamp>=_this.header.end_time){
                        layer.msg('考试结束，自动交卷...', {
                            offset: 't'
                        });
                        _this.submit(1);
                    }
                }

                //自动保存
                if(_this.save_timer%60 == 0  && _this.submiting==false){
                    xingQuestion.submit(0,function () {
                        /*
                        layer.msg('自动保存答案', {
                            offset: 't',
                        });
                        */
                    })
                }

            },1000);
            layer.closeAll();
            window.onbeforeunload = function() {
                _this.close(0);
                return null;
            };
        }
    },
    //暂停作答
    pause:function(show_inco = 1){
        let _this = this;
        if(_this.timer_id != null){
            clearInterval(_this.timer_id);
            _this.timer_id = null;
            if (show_inco){
                layui.use('layer', function() {
                    layer.open({
                        type: 1,
                        title: false,
                        closeBtn: 0,
                        shadeClose: false,
                        scrollbar:false,
                        skin: 'pause',
                        content: '<div class="pause-img"></div><div class="pause-info">休息一下</div><a href="javascript:xingQuestion.start()" class="start-button">继续答题</a>'
                    });
                });
            }
        }
    },
    submitConfirm:function (){
        let _this = this;
        //大模考判断交卷时间
        if(_this.type=='5'){
            if(_this.now_timestamp<_this.header.submit_time){
                layui.use('layer', function() {
                    var layer = layui.layer;
                    let tmp = _this.header.end_time - _this.header.submit_time;
                    if(tmp>60){
                        tmp =parseInt(tmp/60)+'分钟';
                    }else{
                        tmp = tmp+'秒';
                    }
                    layer.msg('未到交卷时间，最多可以提前'+tmp+'交卷', {icon: 7});
                });
                return false;
            }
        }
        layer.confirm('你确定要交卷吗？', {
            btn: ['确定交卷','取消'] //按钮
        }, function(){
            _this.submit(1);
        }, function(){

        });
    },
    //交卷
    submit:function (status=1,okFun=function () {}) {
        let _this = this;
        _this.submiting = true;
        if(status){
            layui.layer.load(1,{ shade: [0.3,'#000']});
        }
        $.ajax({
            type: "POST",
            url:  "/pc/xingQuestion/submit/subject_id/"+subject_id,
            data: {
                report_id:_this.report_id,
                type:_this.type,
                type_param:_this.type_param,
                answer_data:JSON.stringify(_this.getData()),
                duration:_this.last_select_aswer_time,//(_this.last_select_aswer_time>0)?_this.last_select_aswer_time:_this.report_time_long,
                status:status
            },
            dataType:'json',
            success: function (resule) {
                if(resule.status==1){
                    _this.report_id = resule.data.report_id;
                    if(studyTime.type_id == null){
                        studyTime.type_id = resule.data.report_id;
                        studyTime.update();
                    }
                    okFun();
                    if(status==1){
                        _this.pause(0);
                        window.onbeforeunload=null;
                        if(_this.type == 5){
                            location.href = "/pc/xingQuestion/examList/subject_id/"+subject_id;
                        }else{
                            location.href = "/pc/xingQuestion/report/subject_id/"+subject_id+"/report_id/"+resule.data.report_id;
                        }
                        return false;
                    }
                }else{
                    layer.closeAll();
                    layui.use('layer', function() {
                        var layer = layui.layer;
                        layer.msg(resule.info, {icon: 7});
                    });
                }
                _this.submiting = false;
            },
            error:function (XMLHttpRequest, textStatus, errorThrown) {
                layui.use('layer', function() {
                    var layer = layui.layer;
                    layer.msg('网络请求超时', {icon: 7});
                });
                layer.closeAll();
                _this.submiting = false;
            }
        });
    },
    //退出
    close:function(type=1){
        let _this = this;
        layui.layer.load(1,{ shade: [0.3,'#000']});
        this.submit(0,function () {
            if(type == 1){
                window.onbeforeunload=null;
                if(_this.type == '4'){
                    location.href = "/pc/xingQuestion/paperList/subject_id/"+subject_id;
                }else if(_this.type == '5'){
                    location.href = "/pc/xingQuestion/examList/subject_id/"+subject_id+"/type/1";
                }else if(_this.type == '7'){
                    location.href = "/pc/xingQuestion/errorQuesList/subject_id/"+subject_id;
                }else if(_this.type == '8'){
                    location.href = "/pc/xingQuestion/examList/subject_id/"+subject_id+"/type/2";
                }else{
                    location.href = "/pc/xingQuestion/index/subject_id/"+subject_id;
                }
            }else{
                layer.closeAll();
            }
        });
    },
    //选择
    answerCheck:function(obj){
        var obj = $(obj);
        if(obj.hasClass('disabled')){
            return false;
        }
        var answer_key_obj = obj.find('.ques-item-answer-item-index');
        let user_answer = '';
        if(answer_key_obj.hasClass('ques-item-answer-radio')){
            //单选
            if(answer_key_obj.hasClass('checked')){
                //当前选中
                return true;
            }
            obj.siblings().find(".ques-item-answer-item-index").removeClass("checked");
            answer_key_obj.addClass('checked');
            user_answer = answer_key_obj.text();
        }else{
            //复选
            if(answer_key_obj.hasClass('checked')){
                answer_key_obj.removeClass('checked');
            }else{
                answer_key_obj.addClass('checked');
            }
            obj.parent().find(".checked").text(function (index, text) {
                user_answer +=  text+',';
            });
            user_answer = (user_answer.substring(user_answer.length - 1) == ',') ? user_answer.substring(0, user_answer.length - 1) : user_answer;
        }
        obj.parent().parent().data('user_answer',user_answer);
        let time_long = parseInt(obj.parent().parent().data('time_long'))+(this.report_time_long-this.last_select_aswer_time);
        obj.parent().parent().data('time_long',time_long);
        this.last_select_aswer_time = this.report_time_long;
        if(user_answer!=""){
            $("#card_"+obj.parent().parent().data('ques_id')).addClass('checked');
        }else{
            $("#card_"+obj.parent().parent().data('ques_id')).removeClass('checked');
        }
        let now_num = 0;
        obj.parent().parent().parent().find(".ques-item").each(function (i,v) {
            let tmp = $(v).data('user_answer');
            if(tmp!='' && tmp!=null){
                now_num++;
            }
        });
        let module_id = obj.parent().parent().data('module_id');
        let ques_model = obj.parent().parent().data('ques_model');
        $("#module_"+module_id).data('now_num',now_num);
        $("#module_"+module_id).find("span").text(now_num);
        let count=0;
        $(".ques-module-list-item").each(function (i,v){
            if($(v).data('now_num')!=undefined){
                count+=$(v).data('now_num');
            }
        })
        $(".ques-answer-card-title-now").text(count);
        if(this.knows_mode==2 && ques_model=='0'){
            this.answerCheckBeiTi( obj.parent().parent().data('ques_id'));
        }
    },
    answerCheckBeiTi:function (ques_id){
        //背题模式
        if(this.knows_mode==2){
            let ques_item = $("#ques_id_"+ques_id);
            let ques_item_analysis = ques_item.children('.ques-item-analysis');
            let ques_item_answer_item = ques_item.children('.ques-item-answer').children('.ques-item-answer-item');
            let right_answer = ques_item_analysis.children('.ques-item-analysis-sta').find('.right_answer').text();
            ques_item_analysis.show();
            ques_item_answer_item.removeAttr('onclick').addClass('no-select-option');
            let user_answer = '';
            if(ques_item.data('ques_model')=='0'){
                //单选
                let user_answer_obj=  ques_item_answer_item.children('.ques-item-answer-item-index').filter('.checked');
                user_answer = ques_item_answer_item.children('.ques-item-answer-item-index').filter('.checked').text();
                if(right_answer!=user_answer){
                    user_answer_obj.removeClass('checked');
                    user_answer_obj.addClass('errored');
                    ques_item_answer_item.filter('.ques-item-answer-item-'+right_answer).children(".ques-item-answer-item-index").addClass("right");
                    ques_item.addClass('ques-item-error-bg');
                }else{
                    ques_item_analysis.children('.ques-item-analysis-sta').find('.your_answer').removeClass('b').addClass('a');
                    ques_item.addClass('ques-item-right-bg');
                }
            }else{
                //复选
                ques_item_answer_item.each(function(i,v){
                    let index_obj = $(v).children(".ques-item-answer-item-index");
                    let answer = index_obj.text();
                    if(right_answer.indexOf(answer)!==-1){
                        if(index_obj.hasClass('checked')){
                            user_answer+=','+answer;
                        }else{
                            index_obj.addClass('checked');
                        }
                    }else{
                        if(index_obj.hasClass('checked')){
                            index_obj.removeClass('checked');
                            index_obj.addClass('errored');
                            user_answer+=','+answer;
                        }
                    }
                });
                user_answer = user_answer.slice(1);
                ques_item.children('.ques-item-answer-checkbox-comfig').hide();
            }
            ques_item_analysis.children('.ques-item-analysis-sta').find('.your_answer').text(user_answer);

        }
    },
    data2View:function(header,data,type){
        this.report_time_long = header.report_time_long;
        this.last_select_aswer_time = header.report_time_long;
        $("#report_name").html(header.report_name);
        $(".ques-answer-card-title-max").text("/"+header.ques_count);
        var ques_item_tpl = $("#ques_item").html();
        var ques_header_tpl = $("#ques_header").html();
        let _this = this;
        _this.report_id = header.report_id;
        if(type==1){
            $(".ques-module-list").append('<div class="ques-module-list-item now" data-module_id="0" onclick="xingQuestion.moduleChange(this)" id="module_0">'+header.report_name+'[<span>0</span>/'+header.ques_count+'] </div>');
            $(".ques-list").append('<div class="ques-list-module" id="module_list_0"></div>');
            $(".ques-module").hide();
            var view = $("#module_list_0");
            _this.laytpl($("#ques_answer_card_content_item").html()).render({
                module_id:0,
                module_name:header.report_name
            }, function(string){
                $(".ques-answer-card-content").append(string);
            });
            layui.each(data, function(index, item){
                if(item.child==undefined){
                    _this.renderQuesItem(view,ques_item_tpl,item);
                }else{
                    _this.renderQuesHeader(view,ques_header_tpl,item);
                    layui.each(item.child, function(index2, item2){
                        _this.renderQuesItem(view,ques_item_tpl,item2);
                    })
                }
            })
        }else{
            var ques_answer_card_content_item_tpl = $("#ques_answer_card_content_item").html();
            var next_moudel_tpl = $("#next_moudel").html();
            layui.each(data, function(index, module){
                $(".ques-module-list").append('<div class="ques-module-list-item" data-module_id="'+module.module_id+'" onclick="xingQuestion.quesCardClick('+module.module_id+',0)" id="module_'+module.module_id+'">'+module.module_name+'[<span>0</span>/'+module.module_question_count+'] </div>');
                $(".ques-list").append('<div class="ques-list-module" id="module_list_'+module.module_id+'" style="display: none"><div class="ques-list-module-description">'+module.description+'</div></div>');
                var view = $("#module_list_"+module.module_id);
                _this.laytpl(ques_answer_card_content_item_tpl).render({
                    module_id:module.module_id,
                    module_name:module.module_name
                }, function(string){
                    $(".ques-answer-card-content").append(string);
                });
                layui.each(module.module_question, function(index, item){
                    if(item.child==undefined || item.child==null){
                        if(index==0){
                            pre_ques_id = item.ques_id;
                        }
                        _this.renderQuesItem(view,ques_item_tpl,item,module.module_id);
                    }else{
                        _this.renderQuesHeader(view,ques_header_tpl,item);
                        layui.each(item.child, function(index2, item2){
                            if(index==0 && index2==0){
                                pre_ques_id = item.ques_id;
                            }
                            _this.renderQuesItem(view,ques_item_tpl,item2,module.module_id);
                        })
                    }
                })
                if(data[index+1] != undefined){
                    _this.laytpl(next_moudel_tpl).render({
                        module_id:data[index+1].module_id,
                        ques_id:0
                    }, function(string){
                        $("#module_list_"+data[index].module_id).append(string);
                    });
                }
            })
            _this.moduleChange("#module_"+data[0].module_id);
        }
        let tmp_count = {};
        let count = 0;
        $(".ques-item").each(function (i,v) {
            let tmp = $(v).data('user_answer');
            if(tmp!='' && tmp!=null){
                if(tmp_count["module_"+$(v).data("module_id")]!=undefined){
                    tmp_count["module_"+$(v).data("module_id")]+=1;
                }else{
                    tmp_count["module_"+$(v).data("module_id")]=1;
                }
            }
        });
        $.each(tmp_count,function (i,v){
            $("#"+i).data('now_num',v);
            $("#"+i).find("span").text(v);
            count+=v;
        })
        $(".ques-answer-card-title-now").text(count);
    },
    //收藏
    fav:function(ques_id){
        let obj = $('#ques_id_'+ques_id).find(".ques-item-title-right-fav");
        if(obj.hasClass('yes')){
            //取消
            obj.removeClass('yes');
            obj.addClass("no")
            obj.text('收藏');
            var _status = 0;
        }else{
            //收藏
            obj.removeClass('no');
            obj.addClass("yes")
            obj.text('已收藏');
            var _status = 1;
        }
        $.post('/pc/xingQuestion/fav/subject_id/'+subject_id,{ques_id:ques_id,status:_status},function(resule){
            if(resule.status==1){

            }else{
                if(_status==1){
                    obj.removeClass('yes');
                    obj.addClass("no")
                    obj.text('收藏');
                }else{
                    obj.text('取消');
                    obj.removeClass('no');
                    obj.addClass("yes")
                }
                layui.use('layer', function() {
                    var layer = layui.layer;
                    layer.msg(resule.info, {icon: 7});
                });
            }
        },'json');
    },

    renderQuesHeader:function(parentObj,ques_header_tpl,item){
        let _this = this;
        _this.laytpl(ques_header_tpl).render({abstract:item.abstract,header_id:item.header_id}, function(string){
            parentObj.append(string);
        });
    },
    renderQuesItem:function(parentObj,ques_item_tpl,item,module_id=0){
        let _this = this;
        item.module_id=module_id;
        _this.laytpl(ques_item_tpl).render(item, function(string){
            parentObj.append(string);
        });
        $(".ques-answer-card-title-now").text(this.user_answer_count);
        _this.laytpl($("#ques_answer_card_content_item_content").html()).render(item, function(string){
            $("#ques_answer_card_content_item_"+module_id).find(".ques-answer-card-content-item-content").append(string);
        });
    },
    //选项卡点击
    quesCardClick:function(moudle_id,ques_id){
        this.moduleChange('#module_'+moudle_id);
        let ctop = 0;
        if(ques_id!=0){
            ctop = $('#ques_id_'+ques_id).offset().top-200;
        }
        $("html,body").animate({scrollTop: ctop},300);
    },
    //模块导航栏点击
    moduleChange:function(obj){
        $(obj).addClass('now');
        $(obj).siblings().removeClass('now');
        let module_id = $(obj).data('module_id');
        $("#module_list_"+module_id).show();
        $("#module_list_"+module_id).siblings().hide();
    },
    header_index:null,
    showHeader:function(header_id){
        let openHeaderWindow = function(){
            let obj = $("#header_"+header_id).find('.ques-item-header-content');
            let header_content = obj.html();
            let area_height = (obj.height()+200)>window.innerHeight-20?window.innerHeight-20:(obj.height()+200)
            xingQuestion.header_index = layer.open({
                id:'ques_id_header_id_'+header_id,
                type: 1,
                skin: 'layui-layer-rim', //加上边框
                title:'材料(提示：1.鼠标在窗口标题栏拖拽调整位置；2.在窗口右下角拖拽调整大小)',
                shade:0,
                moveOut:true,
                area: [(obj.width()-60)+'px',area_height+'px'], //宽高
                content: '<div class="ques-item-header-content ques-item-title-right-item ques-item-title-right-huaban" style="justify-self: flex-end;"' +
                    ' onclick="javascript:xingQuestion.huaban(\'header_id_'+header_id+'\',0,0)">\n' +
                    '                草稿纸\n' +
                    '            </div>' +
                    '<div class="ques-item-header-content">'+header_content+'</div>',
                resize:true,
                maxmin:true,
                offset:'r',
                cancel: function(index, layero){
                    xingQuestion.header_index=null;
                    layer.close(index)
                    return false;
                },
                resizing: function(layero){
                    $('#ques_id_header_id_'+header_id).find('#sketchpad_header_id_'+header_id).remove();
                }
            });
        }
        if(xingQuestion.header_index!=null){
            let tmp = xingQuestion.header_index;
            xingQuestion.header_index=null;
            layer.close(tmp);
            setTimeout(function () {
                openHeaderWindow()
            },200);
        }else{
            openHeaderWindow();
        }
    },
    huaban_obj:[],
    huaban:function (ques_id,width_offset=0,height_offset=0) {
        let obj = $('#ques_id_'+ques_id);
        let id = "canvas_"+ques_id;
        let width = obj.outerWidth(false)+width_offset
        let height = obj.outerHeight(false)+height_offset;
        if(obj.find('#sketchpad_'+ques_id).length>0){
            obj.find('#sketchpad_'+ques_id).show();
        }else{
            let sketchpad_huaban_tpl = $("#sketchpad_huaban").html();
            this.laytpl(sketchpad_huaban_tpl).render({
                width:width,
                height:height,
                id:id,
                ques_id:ques_id
            }, function(string){
                obj.append(string);
                setTimeout(function (){
                    xingQuestion.huaban_obj[ques_id] = new Sketchpad({
                        element: '#'+id,
                        width: width,
                        height: height,
                        color: '#f8563d',
                        penSize:4
                    });
                },200);
            });
        }
    },
    huabanEraser:function (ques_id) {
        if(xingQuestion.huaban_obj[ques_id].is_eraser===0){
            xingQuestion.huaban_obj[ques_id].is_eraser=1;
            xingQuestion.huaban_obj[ques_id].color='eraser';
            xingQuestion.huaban_obj[ques_id].penSize=20;
            $("#sketchpad_"+ques_id).find('.eraser-icon').addClass('eraser-icon2');
            $("#sketchpad_"+ques_id).find('.eraser-icon').next().addClass('tool-name2');
            $("#canvas_"+ques_id).addClass('cursor');
        }else{
            xingQuestion.huaban_obj[ques_id].is_eraser=0;
            xingQuestion.huaban_obj[ques_id].color='#f8563d';
            xingQuestion.huaban_obj[ques_id].penSize=4;
            $("#sketchpad_"+ques_id).find('.eraser-icon').removeClass('eraser-icon2');
            $("#sketchpad_"+ques_id).find('.eraser-icon').next().removeClass('tool-name2');
            $("#canvas_"+ques_id).removeClass('cursor');
        }
    },
    getTime:function(time) {
        // 转换为式分秒
        let h = parseInt(time / 60 / 60 % 24)
        h = h < 10 ? '0' + h : h
        let m = parseInt(time / 60 % 60)
        m = m < 10 ? '0' + m : m
        let s = parseInt(time % 60)
        s = s < 10 ? '0' + s : s
        // 作为返回值返回
        return h+":"+m+":"+s;
    },
    getData:function() {
        let form_data = [];
        $(".ques-item").each(function (i,v) {
            let data = $(v).data();
            form_data.push({
                ques_id: data.ques_id,
                module_id: data.module_id,
                user_answer: data.user_answer,
                time_long:data.time_long,
                is_mark:data.is_mark
            })
        })
        return form_data;
    },
    timestampToTime:function (timestamp) {
        var date = new Date(timestamp * 1000);//时间戳为10位需*1000，时间戳为13位的话不需乘1000
        var Y = date.getFullYear() + '-';
        var M = (date.getMonth()+1 < 10 ? '0'+(date.getMonth()+1) : date.getMonth()+1) + '-';
        var D = (date.getDate() < 10 ? '0'+(date.getDate()) : date.getDate()) + ' ';
        var h = (date.getHours() < 10 ? '0'+(date.getHours()) : date.getHours()) + ':';
        var m = (date.getMinutes() < 10 ? '0'+(date.getMinutes()) : date.getMinutes()) + ':';
        var s = (date.getSeconds() < 10 ? '0'+(date.getSeconds()) : date.getSeconds());
        return Y+M+D+h+m+s;
    }
}




var xingQuestionReport = {
    is_report_view:0,
    bplayer_list:[],
    aplayer_list:[],
    load:function (report_id,is_wrong,module_id='',ques_id=''){
        this.is_report_view=1;
        let _this = xingQuestion;
        layui.use('layer', function() {
            var layer = layui.layer;
            layer.load(1,{ shade: [0.3,'#000']});
            $.post('/pc/xingQuestion/reportAnalysis/subject_id/'+subject_id,{report_id:report_id,is_wrong:is_wrong},function(resule){
                layer.closeAll();
                if(resule.status==1){
                    layui.use(['layer','laytpl'], function(){
                        _this.laytpl = layui.laytpl;
                        if(resule.data.ques_data!=undefined){
                            _this.data2View(resule.data.header,resule.data.ques_data,1);
                        }else{
                            _this.data2View(resule.data.header,resule.data.paper_data,2);
                        }
                    });
                    $('body').data('vip_status',resule.data.header.vip_status);
                    $('body').data('free_xing_video_num',resule.data.header.free_xing_video_num);

                    setTimeout(function () {
                        if(ques_id!=''){
                            if(module_id!=''){
                                xingQuestion.quesCardClick(module_id,ques_id);
                            }else{
                                xingQuestion.quesCardClick(0,ques_id);
                            }
                        }
                    },100)
                }else{
                    layui.use('layer', function() {
                        var layer = layui.layer;
                        layer.alert(resule.info, {
                            time: 5*1000,
                            success: function(layero, index){
                                var timeNum = this.time/1000, setText = function(start){
                                    layer.title('<span class="layui-font-red">'+ (start ? timeNum : --timeNum) + '</span> 秒后自动返回上一页', index);
                                };
                                setText(!0);
                                this.timer = setInterval(setText, 1000);
                                if(timeNum <= 0){
                                    clearInterval(this.timer);
                                    window.history.back();
                                }
                            },
                            end: function(){
                                clearInterval(this.timer);
                                window.history.back();
                            }
                        });
                    });
                }
            },'json')
        })
    },


    loadData:function (data){
        this.is_report_view=1;
        let _this = xingQuestion;
        $('body').data('vip_status',data.header.vip_status);
        $('body').data('free_xing_video_num',data.header.free_xing_video_num);
        layui.use(['layer','laytpl'], function(){
            _this.laytpl = layui.laytpl;
            if(data.ques_data!=undefined){
                _this.data2View(data.header,data.ques_data,1);
            }else{
                _this.data2View(data.header,data.paper_data,2);
            }
        });
    },

    rate:function (id,score) {
        setTimeout(function () {
            layui.use(['rate'], function(){
                var rate = layui.rate;
                rate.render({
                    elem: '#'+id
                    ,value: score
                    ,readonly: true
                    ,half: true
                    ,text: true
                    ,setText: function(value){ //自定义文本的回调
                        this.span.text(( value + "分"));
                    }
                });
            })
        },1000)
    },
    read:function (id) {
        let obj = $("#"+id);
        let ques_id =obj.parents('.ques-item').data('ques_id');
        let user_analysis_status = obj.parent().data('status');
        let obj_status = obj.data('status');
        let loadding = obj.parent().data('loading');
        if(loadding==1){
            layui.use('layer', function() {
                var layer = layui.layer;
                layer.msg('您点的太快了', {icon: 7});
            });
            return false;
        }

        obj.parent().data('loading',1);
        if(obj_status == user_analysis_status){
            //取消
            obj.removeClass('checked');
            $.post('/pc/Likes/cancel',{type:2,type_id:ques_id},function(resule){
                if(resule.status==1){
                    obj.parent().data('status',0);
                }else{
                    obj.addClass("checked");
                    layui.use('layer', function() {
                        var layer = layui.layer;
                        layer.msg(resule.info, {icon: 7});
                    });
                }
                obj.parent().data('loading',0);
            },'json');
        }else if(obj_status!=user_analysis_status){
            //切换
            obj.siblings('.checked').removeClass('checked');
            obj.addClass("checked");
            $.post('/pc/Likes/like',{type:2,type_id:ques_id,value:obj_status},function(resule){
                if(resule.status==1){
                    obj.parent().data('status',obj_status);
                }else{
                    obj.removeClass("checked");
                    obj.siblings('a[data-status="'+user_analysis_status+'"]').addClass('checked');
                    layui.use('layer', function() {
                        var layer = layui.layer;
                        layer.msg(resule.info, {icon: 7});
                    });
                }
                obj.parent().data('loading',0);
            },'json');
        }
    },
    feedbookView:function (ques_id) {
        var feedbook_tpl = $("#feedbook").html();
        xingQuestion.laytpl(feedbook_tpl).render({ques_id:ques_id}, function(string){
            layer.open({
                type: 1,
                title: '纠错',
                closeBtn: 0,
                shadeClose: true,
                scrollbar:false,
                skin: 'yourclass',
                content: string,
                area:['590px'],
                btn: ['确定','取消'],//按钮
                yes:function (index, layero) {
                    var type = $('#feedbook_form input[name="type"]:checked').val();
                    if(type=='' || typeof type!='string'){
                        layer.msg('请选择类型',{icon: 5,time: 1500});
                        return false;
                    }
                    let sload =layer.load(1,{ shade: [0.3,'#000']});
                    var wrong_content = '【'+type+'】'+$("#feedbook_form .js-text").val();
                    $.post('/pc/comment/add', {type:5,type_id:ques_id, content:wrong_content}, function(res){
                        if(res.status == '1') {
                            ts='<i class="fa fa-check" aria-hidden="true"></i> ';
                            layer.msg('纠错成功',{icon: 6,time: 3000});
                            layer.close(index);
                            layer.close(sload);
                        } else {
                            ts='<i class="fa fa-times" aria-hidden="true"></i> ';
                            layer.msg('纠错失败',{icon: 5,time: 3000});
                            layer.close(sload);
                        }
                    },'json');

                },
                success:function () {
                    layui.use('form', function(){
                        var form = layui.form;
                        form.render();
                    });
                }
            });
        });
    },
    video:function (ques_id,video_type,video_id) {
        let _this = this;
        let free_xing_video_num = $('body').data('free_xing_video_num');
        let vip_status= $('body').data('vip_status');
        let token = $('body').data(video_id);
        $('#video_'+ques_id).children().hide();
        if(token==null || token==''){
            $.getJSON('/Pc/XingQuestion/analysisVideo',{video_type:video_type,video_id:video_id},function(resule){
                if(resule.status==1){
                    $('body').data('free_xing_video_num');
                    token = resule.data;
                    $('body').data(video_id,token);
                    $('#video_'+ques_id).empty();
                    if(video_type==1){
                        _this.openVideoBjy(ques_id,video_id,token);
                    }else{
                        _this.openVideoAli(ques_id,video_id,token);
                    }
                }else{
                    $('#video_'+ques_id).children().show();
                    layer.msg(resule.info,{icon: 5,time: 3000});
                }
            },'json');
        }else{
            $('#video_'+ques_id).empty();
            if(video_type==1){
                _this.openVideoBjy(ques_id,video_id,token);
            }else{
                _this.openVideoAli(ques_id,video_id,token);
            }
        }
    },
    openVideoAli:function (ques_id,video_id,token) {

        this.aplayer_list.push(new Aliplayer({
            id:'video_'+ques_id,
            width: '100%',
            vid:video_id,
            playauth : token,
            useH5Prism:true,
            height:450,
        },function(player){
            layer.restore(index);
        }));
    },
    openVideoBjy:function (ques_id,video_id,token) {
        this.bplayer_list.push(
            new BPlayer({
                container: document.getElementById('video_'+ques_id),
                autoplay: true,
                volume: 1,
                vid:video_id,
                token:token
            }).on('playing', () => {
                let container_id = 'video_'+ques_id;
                xingQuestionReport.bplayer_list.forEach(function (v) {
                    if(v.player.paused===false && v.player.container.id!==container_id){
                        v.player.pause();
                    }
                })
            }).on('first_play', () => {
                let container_id = 'video_'+ques_id;
                xingQuestionReport.bplayer_list.forEach(function (v) {
                    if(v.player.paused===false && v.player.container.id!==container_id){
                        v.player.pause();
                    }
                })
            })
        );
    },
    buyVip:function (){
        var params = {
            type: 2,
            title: '开通会员',
            shadeClose: true,
            scrollbar:false,
            skin: 'layui-layer-bg',
            shade: [0.5, '#000000'],
            area: ['1150px', '600px'],
            content:'/pc/vip/vipQuickPay'
        };
        layui.use('layer', function(){
            layer.open(
                params
            )
        });
        return false;
    },
    showAnalysis:function (ques_id,the) {
        let obj = $("#analysis_"+ques_id);
        if(obj.is(':visible')){
            obj.hide(100);
            $('#analysis_a_'+ques_id).text('展开解析')
        }else{
            obj.show(100);
            $('#analysis_a_'+ques_id).text('收起解析')
        }
    },
    commentList:function (ques_id){
        var params = {
            type: 2,
            title: '视频解析评论列表',
            shadeClose: true,
            skin: 'layui-layer-bg',
            shade: [0.5, '#000000'],
            area: ['800px', '90%'],
            scrollbar:false,
            content:'/pc/comment/lists/type/3/type_id/'+ques_id
        };
        layui.use('layer', function(){
            layer.open(
                params
            )
        });
        return false;
    },
    addComment:function (ques_id){
        var params = {
            type: 2,
            title: '视频解析评论列表',
            shadeClose: true,
            skin: 'layui-layer-bg',
            shade: [0.5, '#000000'],
            area: ['800px', '500px'],
            scrollbar:false,
            content:'/pc/comment/add/type/3/type_id/'+ques_id
        };
        layui.use('layer', function(){
            layer.open(
                params
            )
        });
        return false;
    },
    noteView:function (ques_id){
        let text = $.trim($("#ques_note_"+ques_id).text());
        $("#ques_note_"+ques_id)
            .empty()
            .append("<textarea id='ques_note_content_"+ques_id+"' class='ques-item-analysis-note-content-textarea'>"+text+"</textarea>")
            .next(".report-content-button")
            .show()
            .prev()
            .prev()
            .find("a")
            .hide(0)
        ;
    },
    note:function (ques_id) {
        let content = $.trim($('#ques_note_content_'+ques_id).val());
        $.post('/pc/xingQuestion/note/subject_id/'+subject_id,{ques_id:ques_id,content:content},function(resule){
            if(resule.status==1){
                layui.use('layer', function() {
                    var layer = layui.layer;
                    layer.msg(resule.info, {icon: 1});
                });
            }else{
                layui.use('layer', function() {
                    var layer = layui.layer;
                    layer.msg(resule.info, {icon: 7});
                });
            }
        },'json');
    },
    toggleAnalysis:function (ques_id) {
        let ques_item = $("#ques_id_"+ques_id);
        let ques_item_analysis_content = ques_item.children('.ques-item-analysis').children('.ques-item-analysis-content');
        let ques_item_analysis_commit = ques_item.children('.ques-item-analysis').children('.ques-item-analysis-commit');
        let ques_item_analysis_video = ques_item.children('.ques-item-analysis').children('.ques-item-analysis-video');

        if(ques_item_analysis_content.is(':hidden')){
            ques_item_analysis_content.show(50);
            ques_item_analysis_commit.show(50);
            ques_item_analysis_video.show(50);
            ques_item.children('.ques-item-analysis').find('.ques-item-analysis-sta-action-button').text('收起解析⏶');
        }else{
            ques_item_analysis_content.hide(50);
            ques_item_analysis_commit.hide(50);
            ques_item_analysis_video.hide(50);
            ques_item.children('.ques-item-analysis').find('.ques-item-analysis-sta-action-button').text('展开解析⏷');
        }

    }
};

$(function() {
    function topLock(obj){
        var st = Math.max(document.body.scrollTop || document.documentElement.scrollTop);
        if (st > parseInt(obj.attr('otop'))+100) {
            if (obj.css('position') != 'fixed') obj.css({
                'position': 'fixed',
                top: 0,
                'z-index':999
            });
        } else if (obj.css('position') != 'static') obj.css({
            'position': 'static'
        });
    }
    var dv = $('#fixedMenu');
    if(dv.length>0){
        dv.attr('otop', dv.offset().top); //存储原来的距离顶部的距离
    }
    var dv2 = $('.ques-module_fixed');
    if(dv2.length>0){
        dv2.attr('otop', dv2.offset().top); //存储原来的距离顶部的距离
    }
    $(window).scroll(function() {
        if(dv2.length>0){
            topLock(dv2)
        }
        if(dv.length>0){
            topLock(dv)
        }
    });
});
function buyVipCallback(){
    window.onbeforeunload=null;
    if(xingQuestionReport.is_report_view!==1){
        xingQuestion.submit(0,function () {
            window.location.reload();
        })
    }else{
        window.location.reload();
    }
}
/**
$(document).on('selectstart',function () {
    return false;
});
**/

