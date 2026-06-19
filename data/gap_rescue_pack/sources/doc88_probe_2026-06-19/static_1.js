var Reader = function(){}; 
Reader.m_rightDHeight = 318;
Reader.m_rightTopHeight = 190;
Reader.m_secAdLoad = false;
Reader.m_eventPosition = 0;
Reader.m_rightLoadMoreIf = 0;
Reader.m_lastScrollY = 0;
Reader.m_adHost = "//www.doc88.com/ads/" ;
Reader.m_adInitIf = true;
Reader.m_listAdArray = new Array();
function Map(){

	this.keys = new Array(); 
	
	this.data = new Object();
	
	var toString = Object.prototype.toString;
	
	/**
	 * 当前Map当前长度
	 */
	this.size = function(){
		return this.keys.length;
	};
	
	/**
	 * 添加值
	 * @param {Object} key
	 * @param {Object} value
	 */
	this.put = function(key, value){
		if(this.data[key] == null){
			this.data[key] = value;
		}
		this.keys.push(key);
	};
	/**
	 * 根据当前key获取value
	 * @param {Object} key
	 */
	this.get = function(key){
		return this.data[key];
	};
	/**
	 * 根据当前key移除Map对应值
	 * @param {Object} key
	 */
	this.remove = function(key){
		var index = this.indexOf(key);
		if(index != -1){
			this.keys.splice(index, 1);
		}
		this.data[key] = null;
	};
	/**
	 * 清空Map
	 */
	this.clear = function(){
		for(var i=0, len = this.size(); i < len; i++){
			var key = this.keys[i];
			this.data[key] = null;
		}
		this.keys.length = 0;
	};
	/**
	 * 当前key是否存在
	 * @param {Object} key
	 */
	this.containsKey = function(key){
		return this.data[key] != null;
	};
	/**
	 * 是否为空
	 */
	this.isEmpty = function(){
		return this.keys.length === 0;
	};
	/**
	 * 类型Java中Map.entrySet
	 */
	this.entrySet = function(){
		var size = this.size();
		var datas = new Array(size);
		for (var i = 0, len = size; i < len; i++) {
			var key = this.keys[i];
			var value = this.data[key];
			datas[i] = {
				'key' : key,
				'value':value	
			}
		}
		return datas;
	};
	/**
	 * 遍历当前Map
	 * var map = new Map();
	 * map.put('key', 'value');
	 * map.each(function(index, key, value){
	 * 		console.log("index:" + index + "--key:" + key + "--value:" + value)
	 * })
	 * @param {Object} fn
	 */
	this.each = function(fn){
		if(toString.call(fn) === '[object Function]'){
			for (var i = 0, len = this.size(); i < len; i++) {
				var key = this.keys[i];
				fn(i, key, this.data[key]);
			}
		}
		return null;
	};
	/**
	 * 获取Map中 当前key 索引值
	 * @param {Object} key
	 */
	this.indexOf = function(key){
		var size = this.size();
		if(size > 0){
			for(var i=0, len=size; i < len; i++){
				if(this.keys[i] == key)
				return i;
			}
		}
		return -1;
	};
	/**
	 * Override toString
	 */
	this.toString = function(){
		var str = "{";
		for (var i = 0, len = this.size(); i < len; i++, str+=",") {
			var key = this.keys[i];
			var value = this.data[key];
			str += key + "=" + value; 
		}
		str = str.substring(0, str.length-1);
		str += "}";
		return str;
	};
	/**
	 * 获取Map中的所有value值(Array)
	 */
	this.values = function(){
		var size = this.size();
		var values = new Array();
		for(var i = 0; i < size; i++){
			var key = this.keys[i];
			values.push(this.data[key]);
		}
		return values;
	};
	
}

var globePageWidth = 988;
var m_ie6=!-[1,]&&!window.XMLHttpRequest;
var staticUrl = "https://www.doc88.com/";
var skinImgIndex = 0;
var skinColorIndex = 0;
var firstOpenSkin = true;
function initSkin()
{
	//$("#skin-list-img").append(getImgColorSkinHtml(staticUrl+'assets/images/skin/0701/skin-0701-img.jpg',3,'#de1a17','建党100周年'));
	$("#skin-list-img").append(getImgSkinHtml(staticUrl+'assets/images/skin/skin-paper1-img.png','素色纸张'));
	
	//$("#skin-list-img").append(getImgColorSkinHtml(staticUrl+'assets/images/skin/festival/skin-festival-lantern-img.png',3,'#ffe8c6','元宵佳节'));
	//$("#skin-list-img").append(getImgColorSkinHtml(staticUrl+'assets/images/skin/festival/skin-festival-mayday-img.jpg',3,'#b3caa0','五一佳节'));
	//$("#skin-list-img").append(getImgColorSkinHtml(staticUrl+'assets/images/skin/festival/skin-festival-dragon-img.jpg',3,'#f9fcdf','端午佳节'));
	//$("#skin-list-img").append(getImgColorSkinHtml(staticUrl+'assets/images/skin/skin-2018/skin-2018-img.png',3,'#fdedd6','狗年大吉')); 
	//$("#skin-list-img").append(getImgColorSkinHtml(staticUrl+'assets/images/skin/skin-2018-img.png',3,'#fbf4f0','道客十年')); 
	    
	//#f5f0da
	//$("#skin-list-img").append(getImgColorSkinHtml(staticUrl+'assets/images/skin/skin-20141001-img.png',3,'#f5f0d9','喜迎国庆'));
	//$("#skin-list-img").append(getImgColorSkinHtml(staticUrl+'assets/images/skin/skin-20140908-img.png',3,'#f5f0d9','中秋佳节'));
	
	//$("#skin-list-img").append(getImgColorSkinHtml(staticUrl+'assets/images/skin/skin-20150219-img.png',3,'#f5f0d9','喜迎新春'));
	$("#skin-list-img").append(getImgSkinHtml(staticUrl+'assets/images/skin/skin-paper3-img.png','深色纸张'));
	$("#skin-list-img").append(getImgSkinHtml(staticUrl+'assets/images/skin/skin-paper2-img.png','牛皮纸张'));
	$("#skin-list-img").append(getImgSkinHtml(staticUrl+'assets/images/skin/skin-paper4-img.png','个性纸张'));
	$("#skin-list-img").append(getImgSkinHtml(staticUrl+'assets/images/skin/skin-blackboard-img.png','再回课堂'));
	$("#skin-list-img").append(getImgSkinHtml(staticUrl+'assets/images/skin/skin-birthday-img.png','生日礼物'));
	$("#skin-list-img").append(getImgSkinHtml(staticUrl+'assets/images/skin/skin-wedding-img.png','我结婚啦'));
	
	
	$("#skin-list-img").append(getImgSkinHtml(staticUrl+'assets/images/skin/skin-modern-img.png','摩登男女'));
	$("#skin-list-img").append(getImgSkinHtml(staticUrl+'assets/images/skin/skin-LV-img.png','我爱驴牌'));
	$("#skin-list-img").append(getImgSkinHtml(staticUrl+'assets/images/skin/skin-cat1-img.png','可爱猫咪'));
	$("#skin-list-img").append(getImgSkinHtml(staticUrl+'assets/images/skin/skin-dance1-img.png','现代舞者'));
	$("#skin-list-img").append(getImgSkinHtml(staticUrl+'assets/images/skin/skin-texture1-img.png','雪青机理'));
	$("#skin-list-img").append(getImgSkinHtml(staticUrl+'assets/images/skin/skin-texture8-img.png','群青花纹'));
	$("#skin-list-img").append(getImgSkinHtml(staticUrl+'assets/images/skin/skin-texture9-img.jpg','古典画布'));
	$("#skin-list-img").append(getImgSkinHtml(staticUrl+'assets/images/skin/skin-texture2-img.png','传统纹理'));
	$("#skin-list-img").append(getImgSkinHtml(staticUrl+'assets/images/skin/skin-texture3-img.png','时尚鱼纹'));
	
	$("#skin-list-img").append(getImgSkinHtml(staticUrl+'assets/images/skin/skin-black1-img.png','黑色细纹'));
	$("#skin-list-img").append(getImgSkinHtml(staticUrl+'assets/images/skin/skin-texture4-img.png','抽象星云'));
	$("#skin-list-img").append(getImgSkinHtml(staticUrl+'assets/images/skin/skin-texture5-img.png','蓝色科幻'));
	$("#skin-list-img").append(getImgSkinHtml(staticUrl+'assets/images/skin/skin-texture6-img.png','卡通图案'));
	$("#skin-list-img").append(getImgSkinHtml(staticUrl+'assets/images/skin/skin-texture7-img.png','小小愿望'));
	$("#skin-list-img").append(getImgSkinHtml(staticUrl+'assets/images/skin/skin-fur1-img.png','浅色皮面'));
	      
	$("#skin-list-img").append(getImgSkinHtml(staticUrl+'assets/images/skin/skin-cloth1-img.png','灰色麻布'));
	$("#skin-list-img").append(getImgSkinHtml(staticUrl+'assets/images/skin/skin-bamboo-img.png','实木底纹'));
	$("#skin-list-img").append(getImgSkinHtml(staticUrl+'assets/images/skin/skin-wood-img.png','浅色木纹'));
	$("#skin-list-img").append(getImgSkinHtml(staticUrl+'assets/images/skin/skin-rockwall-img.jpg','坚实墙壁'));
	$("#skin-list-img").append(getImgSkinHtml(staticUrl+'assets/images/skin/skin-stonewall-img.png','深色石壁'));
	$("#skin-list-img").append(getImgSkinHtml(staticUrl+'assets/images/skin/skin-blackmetal-img.png','黑色金属'));
	
	$("#con_skins_1").width(165*$("#skin-list-img").children().length);
	
	
	$("#skin-list-color").append(getColorSkinHtml('#ffffff','纯白无色'));
	$("#skin-list-color").append(getColorSkinHtml('#d6e6d5','轻柔淡绿'));
	$("#skin-list-color").append(getColorSkinHtml('#d8ae92','清淡棕色'));
	$("#skin-list-color").append(getColorSkinHtml('#ffb3a7','粉红妃色'));
	$("#skin-list-color").append(getColorSkinHtml('#e0eee8','淡青灰色'));
	
	$("#skin-list-color").append(getColorSkinHtml('#e4c6d0','藕荷紫色'));
	$("#skin-list-color").append(getColorSkinHtml('#665757','黝黑肤色'));
	$("#skin-list-color").append(getColorSkinHtml('#6b6882','淡青黑色'));
	$("#skin-list-color").append(getColorSkinHtml('#758a99','墨灰颜色'));
	$("#skin-list-color").append(getColorSkinHtml('#88ada6','苍翠水色'));
	
	$("#skin-list-color").append(getColorSkinHtml('#f3d3e7','淡彩水红'));
	$("#skin-list-color").append(getColorSkinHtml('#d3e0f3','淡青水色'));
	$("#skin-list-color").append(getColorSkinHtml('#a4e2c6','艾草绿色'));
	
	$("#skin-list-color").append(getColorSkinHtml('#bbcdc5','蟹壳青色'));
	$("#skin-list-color").append(getColorSkinHtml('#424c50','鸦羽紫青'));
	
		
	$("#con_skins_2").width(165*$("#skin-list-color").children().length);
	
	$("#skin-list-img li").click(function()
	{
		$(".skin-list li").removeClass("current");
		$(this).addClass("current");
		var m_type = $(this).attr("mytype");
		var m_color = $(this).attr("mycolor");
		var m_imgNum = $(this).attr("mynum");
		var m_bg = $(this).find("img").attr("src").replace("-img","");
		var $body = $(document.body);
		if (window.frames.length != parent.frames.length) {
		　　$body = $(window.parent.document.body);
		}
		if(m_type==1)
		{
			$body.css("background-color",m_color);
			$body.css("background-repeat","no-repeat");
			$body.css("background-position","center top");
			if(m_imgNum==3)
			{
			    m_bg = $(this).find("img").attr("src").replace("-img","-"+globePageWidth);
			    $body.css("background-image","url("+m_bg+")");
			}
			else
			{
				//$("#header").css("background","rgba(0,0,0,0.7)");
			}
		}
		else
		{
			$body.css("background-repeat","repeat");
		}
		$body.css("background-image","url("+m_bg+")");
		if(m_bg.indexOf("skin-paper1")==-1)
		{
		   $(".commonbox1").addClass("commonboxbg");
		}
		else
		{
		   $(".commonbox1").removeClass("commonboxbg");
		}
		setCookie("BG_TYPE",0,30*24);
		setCookie("BG_IMG",m_bg,30*24);
		setCookie("BG_IMG_TYPE",m_type,30*24);
		setCookie("BG_COLOR",m_color,30*24);
		setCookie("BG_ID",$(this).attr("id"),30*24);
	});
	$("#skin-list-color li").click(function()
	{
		if( $(this).attr('id')=='customColorLi') {
			return;
		}
		$(".skin-list li").removeClass("current");
		$(this).addClass("current");
		var m_color = $(this).children("div").children("div").css("backgroundColor");
		var $body = $(document.body);
		if (window.frames.length != parent.frames.length) {
		　　$body = $(window.parent.document.body);
		}
		$body.css("backgroundColor", m_color); 
		$body.css("background-image","url()");
		$(".commonbox1").addClass("commonboxbg");
		setCookie("BG_TYPE",1,30*24);
		setCookie("BG_COLOR",m_color,30*24);
		setCookie("BG_ID",$(this).attr("id"),30*24);
	});
		
	$("#skin_panel_1").width(globePageWidth-60);
	$("#skin_panel_2").width(globePageWidth-60);
	$('.addcolor,.pink-color').css('backgroundColor', getCookie("CUS_BG_COLOR"));
	$('.pink-color').val(getCookie("CUS_BG_COLOR").substring(1));
}
//顶部登陆表单弹出
$(document).ready(function(){

	var m_mycolorHtml ='<li id="customColorLi">'+
	          '<div class="skinimg">'+
	          '<input class="pink-color jscolor {onFineChange:\'colorUpdates(this)\',position:\'right\',padding:0, shadow:false,borderWidth:0, backgroundColor:\'transparent\', insetColor:\'transparent\'}" value="ffffff">'+
	            '<div class="addcolor"></div>'+
	            '<span class="checked"></span>'+
	          '</div>'+
	          '<p>自定义颜色</p>'+
	        '</li>';
	$("#skin-list-color").append(m_mycolorHtml);	
    if (typeof(global_page) == "undefined") {
	   global_page = "";
    }
	//初始化皮肤
	if(global_page!="home")
	{
		$(".skintips .close").click(function(){
			$(".skintips").hide();
		});
		$(".skintips .into").click(function(){
		
			$(".topshop").slideToggle();
			loadShowSkinImg();
			$(".skintips").hide();
			try{
				Viewer.m_setRightPanel();
			}
			catch(e)
			{
			}
			firstOpenSkin = false;
		});
		$(".skin-peeler").click(function(){
			showSkinSet();
		});
		$(".prevskin").click(function(){
			
			if(!$("#con_skins_1").is(":hidden"))
			{
			  $("#skin_panel_1").animate({scrollLeft:"-=160"},200);
			}
			else
			{
			  $("#skin_panel_2").animate({scrollLeft:"-=160"},200);
			}
		});
		$(".nextskin").click(function(){
				
			if(!$("#con_skins_1").is(":hidden"))
			{
				$("#skin_panel_1").animate({scrollLeft:"+=160"},200);
				loadShowSkinImg();
			}
			else
			{
				$("#skin_panel_2").animate({scrollLeft:"+=160"},200);
			}
		});
		
	}
	
	
	$("#gotop").click(function(){ $(window).scrollTop(0);});
	if(screen.width>1024)
	{
		$("#gotop").show();
	}
	$(window).bind("scroll", function(event){
		var Y=$(this).scrollTop();
	    if(Y>10)
		{
			$(".topshop").slideUp(10);
			$(".skintips").hide();
			$(".colorpicker").hide();
		}
	});
	
	var m_showSkinTip = getCookie("ShowSkinTip_1");
	if(m_showSkinTip!=1)
	{
		setCookie("ShowSkinTip_1",1,30*24);
		$(".skintips").show();
	}
	if(global_page!="reading")
	{
	   	$(".skintips").hide();
		$(".skin-peeler").hide();
	}
	if(global_page=="list")
	{
		if(IsPC())
		{
			Reader.m_initAd();
		}
	}
	var m_bgtype = getCookie("BG_TYPE");
	if(m_bgtype==""||m_bgtype==0)
	{
	    var m_bgid = getCookie("BG_ID");
	   var m_bgimg = getCookie("BG_IMG");
	   if(m_bgimg=="")
	   {
	      m_bgid = "skin-img-li-1";
	   }
	  	if(m_bgimg!=""&&m_bgimg.indexOf("skin-paper1")==-1)
		{
		   $(".commonbox1").addClass("commonboxbg");
		}
		$("#"+m_bgid).addClass("current");
	}
	else if(m_bgtype==1)
	{
	    var m_bgid = getCookie("BG_ID");
	    $(".commonbox1").addClass("commonboxbg");
	    $("#"+m_bgid).addClass("current");
	}
	
	$(".login a").mousemove(function(){
		$(this).addClass("current");
		$(this).parent().find(".downmenu1").slideDown("fast",function(){document.getElementById("loginname").focus();})

	});
	$(".login").mouseleave(function(){
		$(this).find("a").removeClass("current");
		$(this).find(".downmenu1").slideUp("fast")
	});
});
function showSkinSet()
{
	if(firstOpenSkin)
	{
		initSkin();
	}
	firstOpenSkin = false;
	$(".topshop").slideToggle();
	loadShowSkinImg();
	try{
		Viewer.m_setRightPanel();
	}
	catch(e)
	{
	}
	$(this).blur();
	$(".skintips").hide();
}
function colorUpdates(hex){
	$('.addcolor').css('backgroundColor', '#' + hex);
	var $body = $(document.body);
	if (window.frames.length != parent.frames.length) {
	　　$body = $(window.parent.document.body);
	}
	$body.css('backgroundColor',('#' + hex));
	$body.css("background-image","url()");
	setCookie("BG_TYPE",1,30*24);
    setCookie("BG_COLOR",'#' + hex,30*24);
	setCookie("CUS_BG_COLOR",'#' + hex,30*24);
	setCookie("BG_ID",$(this).attr("id"),30*24);
}
function loadShowSkinImg()
{
	if(m_ie6)
	{
	  return;
	}
	var maxIndex = $("#skin_panel_1").scrollLeft()/160+8;
	var eachIndex = 0;
	$("#skin-list-img li").each(function()
	{
	    eachIndex++;
	    if(eachIndex<=maxIndex)
	    {
		    if($(this).find("img").length==0)
		    {
		        var imgSrc = $(this).attr("skinImg");
		
			$(this).find(".skinimg").append('<img src="'+imgSrc+'">');
		    }
	    }
	});

}
function loadCss(path) {
    var cssTag = document.getElementById('pageSkin');
    var head = document.getElementsByTagName('head').item(0);
    if (cssTag) head.removeChild(cssTag);
    css = document.createElement('link');
    css.href = path;
    css.rel = 'stylesheet';
    css.type = 'text/css';
    css.id = 'loadCss';
    head.appendChild(css);
}
function loadScript(src,callback, charset)
{
	var script = document.createElement('script');   
	script.setAttribute('language', 'javascript');   
	if (charset) {   
		script.setAttribute('charset', charset);   
	}   
	script.setAttribute('src', src);   
	document.getElementsByTagName("head")[0].appendChild(script);   
	if(document.all) {   
		script.onreadystatechange = function() {   
			if(this.readyState == 4 || this.readyState == 'complete' || this.readyState == 'loaded') {   
				callback();   
			}   
		};   
	} else {   
		script.onload = function() {   
			callback();   
		};   
	}   
}
function getImgSkinHtml(img,title)
{
	skinImgIndex++;
    var m_html = '<li id="skin-img-li-'+skinImgIndex+'" type="0" skinImg="'+img+'">'+
      '<div class="skinimg">';
		m_html+='<img src="'+img+'"/>';
        m_html+='<span class="checked"></span>'+
      '</div>'+
      '<p>'+title+'</p>'+
    '</li>';
    return m_html;
}
function getImgColorSkinHtml(img,imgNum,color,title)
{
	skinImgIndex++;
   var m_html = '<li id="skin-img-li-'+skinImgIndex+'" mytype="1" mynum="'+imgNum+'" mycolor="'+color+'"  skinImg="'+img+'">'+
      '<div class="skinimg">';
         if(m_ie6)
	{
   	m_html+='<img src="'+img+'"/>';
	}
        m_html+='<span class="checked"></span>'+
      '</div>'+
      '<p>'+title+'</p>'+
    '</li>';
    return m_html;
}
function getColorSkinHtml(color,title)
{
	skinColorIndex++;
var m_html = '<li id="skin-color-li-'+skinColorIndex+'">'+
      '<div class="skinimg">'+
        '<div style="background:'+color+'"></div>'+
        '<span class="checked"></span>'+
      '</div>'+
      '<p>'+title+'</p>'+
    '</li>';
    return m_html;
}

	    
//顶部分类信息弹出
$(document).ready(function(){
	$(".bookslist").mousemove(function(){
		$(this).find(".downmenu2").slideDown("fast");
	});
	$(".header").mouseleave(function(){
		$(this).find(".downmenu2").hide();
	});
});
$(document).ready(function(){
	$(".commonlist1>li").mouseover(function(){
	$(this).addClass("over");
	}).mouseout(function(){
		$(this).removeClass("over");
	});
	$(".commonlist1>li:even").addClass("alt")

});
// Tabs
function setTab(name,cursel,n){
 for(i=1;i<=n;i++){
  var menu=document.getElementById(name+i);
  var con=document.getElementById("con_"+name+"_"+i);
  menu.className=i==cursel?"current":"";
  con.style.display=i==cursel?"block":"none";
 }
}

$(document).ready(function(){

	
	// 用户资料展开
	
    $(".usercard .drop").click(function(){
	if($(this).parent().find(".dropbox").is(":hidden"))
	{
	     $(".usercard .drop").attr("title","收起");    
	}
	else
	{
	    $(".usercard .drop").attr("title","展开");
	}
        $(this).parent().find(".dropbox").slideToggle("fast");
    });
	/**
	$("#switch1").click(function(){
		$("#switch2").show();
		$(this).parent().find(".docoutline").slideDown("fast");
		$(this).hide();
	});
	$("#switch2").click(function(){
		$(this).hide();
		$(this).parent().parent().find(".docoutline").slideUp("fast",function(){$("#switch1").show();});
	
	});
	**/
});
/* Table 各行换色 */
$(document).ready(function(){
	// Table zebra lists
	$(".tbllist1 tbody tr").mouseover(function()
	{
	$(this).addClass("over");
	}).mouseout(function(){
		$(this).removeClass("over");
	});
	$(".tbllist1 tbody tr:even").addClass("alt");
});
function setDocImg(siteUrl)
{
	var imgA = document.getElementsByTagName("A");
	for(var i=0;i<imgA.length;i++)
	{
		var orig=imgA[i].getAttribute('orig');
		if(orig)
		{
			if(siteUrl+"/"!=orig)
			{
				imgA[i].style.backgroundImage='url('+orig+')';
			}
		}
	}
}
function getCookie(m_name)
{
	var m_cValue = "";
	var m_cookies = document.cookie.split('; ');
		for (var i = 0, l = m_cookies.length; i < l; i++) {
			var m_parts = m_cookies[i].split('=');
			if (m_parts[0]== m_name) {
				if(m_parts.length>1)
				{
					m_cValue =  unescape(m_parts[1]);
				}
			}
		}
	if(m_cValue==null||m_cValue=='null')
	{
		m_cValue="";
	}
	return m_cValue;
}
function setCookie(m_name,m_value,m_objHours)
{
	delCookie(m_name);
	var m_name = escape(m_name);
    var m_value = escape(m_value);
	m_path = "/";
    m_path = m_path == "" ? "" : ";path=" + m_path;
	
	if(m_objHours > 0){  
        var m_date = new Date();
        var m_ms = m_objHours*3600*1000;
        m_date.setTime(m_date.getTime() + m_ms);
		document.cookie = m_name + "=" + m_value  + m_path+"; expires=" + m_date.toGMTString();
   }
   else
   {
	   document.cookie = m_name + "=" + m_value  + m_path;
   } 
}
function delCookie(m_name)
{
    var m_exp = new Date();
    m_exp.setTime(m_exp.getTime() - 1);
    document.cookie= m_name + "=;expires="+m_exp.toGMTString();
}

function checkVersion(type){
  if(type == 'new'){
    location.href="/uc/usr_center.php?act=doc_index&vs=new"
  }else{

    location.href="/uc/usr_center.php"
  }
  setCookie('vs',type)
}

function getLoginBar(divId)
{
    $.ajax({
        url: "/member.php?act=bar",
        dataType:  'html',
        success: function(msg){
            $("#"+divId).html(msg);
        }
    });
}
function checkCode(obj,tipImg)
{
     if(obj.value.length==4)
     {
	     $.ajax({
	        url: "/member.php?act=check_valide&checkcode="+obj.value,
	        dataType:  'html',
	        success: function(msg){
		     $("#"+tipImg).show();
		    if(msg==0)
	                $("#"+tipImg).addClass('green').html("&#xe62e;");
		    else
		       $("#"+tipImg).addClass('red').html("&#xe62f;");
	        }
	    });
    }
    else
    {
       $("#"+tipImg).hide();
    }
}
function setSearchHistory(m_keyword)
{
	if(!window.localStorage)
	{
		return;
	}
	m_keyword = m_keyword.replace(",","");
	if(m_keyword==null||m_keyword=="")
	{
		return;
	}
	var m_sh_keyword = localStorage.getItem("SH_KEYWORD");
	if(m_sh_keyword==null)
	{
		m_sh_keyword = "";
	}
	if(m_sh_keyword!="")
	{
		m_sh_keyword = m_sh_keyword.replace(m_keyword+",","");
	}
	m_sh_keyword = m_keyword+","+m_sh_keyword;
	var m_keywordArray = m_sh_keyword.split(",");
	if(m_keywordArray.length>10)
	{
		var m_lastKeyword = m_keywordArray[m_keywordArray.length-2];
		m_sh_keyword = m_sh_keyword.replace(m_lastKeyword+",","");
	}
	localStorage.setItem("SH_KEYWORD",m_sh_keyword);
}
 function search_submit(){
	keyword = document.getElementById("keyword").value;
	// var regEx = /[\^\{\}\?\*\\]/g;
	// keywordnew = keyword.replace(regEx, "");
	// regEx = /[\[\]\(\)\/]/g;
	// keywordnew = keywordnew.replace(regEx, " ");
	// if(keyword != keywordnew){
	// 	keyword = keywordnew;
	// 	document.getElementById("keyword").value = keyword;
	// }
	if(keyword == ""){
		document.getElementById("keyword").focus();
		return false;
	}
	setSearchHistory(keyword);
	var searchForm = document.getElementById('searchForm');
	searchForm.action='/tag/'+encodeURIComponent(keyword);
    searchForm.target="_blank";
	
	return true;
}
function IsPC()  
{  
           var userAgentInfo = navigator.userAgent;  
           var Agents = new Array("Android", "iPhone", "SymbianOS", "Windows Phone", "iPad", "iPod");  
           var flag = true;  
           for (var v = 0; v < Agents.length; v++) {  
               if (userAgentInfo.indexOf(Agents[v]) > 0) { flag = false; break; }  
           }  
           return flag;  
} 
var bookPanelMap = new Map();
function loadDocMore(pc_id,page)
{
	var books = $("#books_"+pc_id);
	if(books.attr("loading")=="true")
		return;
	books.attr("loading","true");
	 $.ajax({
			url: "/doc.php?act=hcd&curpage="+page+"&pc_id="+pc_id+"&type=1",
			dataType:"html",
			cache:false,
			async: true,
			success: function(msg)
			{
			
				books.attr("loading","false");
				books.attr("page",page);
				books.find("ul").append(msg);
				
				var m_w = books.find("ul").children().length*220;
				books.find("ul").width(m_w);
				if(!IsPC())
				{
					$("#books_"+pc_id).width(m_w);
					bookPanelMap.get("P_"+pc_id).refresh();
				}
			
			}
		});
}
function left(books){

	if(books.is(":animated"))
		return false;
	books.animate({scrollLeft:"-=220"},500);
}
function right(books)
{
	if(books.is(":animated"))
		return false;
	books.animate({scrollLeft:"+=220"},500);
	if(books.attr("loading")=="true")
		return;
	var page = parseInt(books.attr("page"));
	var pc_id = books.attr("pc_id");
	if(books.width()+books.scrollLeft()+10>=books.find("ul").width())
	{
		loadDocMore(pc_id,page+1);
	}
}
var loadedNum = 0;
function loadDoc()
{
	if(loadedIndex>classArray.length-100)
	{
		$(".loadings").html("抱歉，没有更多了");
		$(".loadings").css("cursor","default");
		return;
	}
	if(loadingState)
	{
		return;
	}
	loadedIndex++;
	var pc_array = classArray[loadedIndex].split(":");
	var pc_id = pc_array[0];

	var pc_name = encodeURIComponent(pc_array[1]);
	if(loadedPcIds.indexOf(pc_id+",")!=-1)
	{
	
	    loadDoc();
	    return;
	}
	$(".loadings").html("<img src='"+staticUrl+"assets/images/homeload.gif'/>");
	loadingState = true;
	loadedPcIds+=pc_id+",";
    $.ajax({
		url: "/doc.php?app="+app+"&act=hcd&curpage=1&pc_id="+pc_id+"&pc_name="+pc_name,
		dataType:"html",
		cache:false,
		async: true,
		success: function(msg)
		{
			$(".loadings").html("加载更多...");
			if(msg=="")
			{
			   loadingState = false;
			   loadDoc();
			   return ;
			}
			loadedNum++;
			loadingState = false;
			$('#homedoclist').append(msg);
			if(!IsPC())
			{
				doc_Scroll = new IScroll('#wrapper_'+pc_id, { eventPassthrough: true, scrollX: true, scrollY: false, preventDefault: false });
				doc_Scroll.on('scroll', function(){});
				doc_Scroll.on('scrollEnd', function(){
					var cur_Scroll = bookPanelMap.get("P_"+pc_id);
					if(cur_Scroll.x-2<cur_Scroll.maxScrollX)
					{
						var page = parseInt($("#books_"+pc_id).attr("page"));
						loadDocMore(pc_id,page+1);
					}
				});
				bookPanelMap.put("P_"+pc_id,doc_Scroll);
			}

			$('.hprev').click(function(){left($(this).parent().find("div"));});
			$('.hnext').click(function(){right($(this).parent().find("div"));});
			if($(document).height()<=$(window).height()+100)
			{
				if(loadedNum%5==0)
				{
					return;
				}
				loadDoc();
			}
			else
			{
			    if(loadedNum<5)
			    {
					loadDoc();
				}
			}
		}
	});
}
Reader.m_initAd = function()
{			
		
	$("#adtop").html('<iframe style="margin-top:10px;" id="ad_iframe_top" width="100%" src="'+Reader.m_listAdArray[0]+'" height="90" frameborder="0" scrolling="no"></iframe>');
	$("#adbottom").html('<iframe style="margin-top:10px;" id="ad_iframe_top" width="100%" src="'+Reader.m_listAdArray[1]+'" height="90" frameborder="0" scrolling="no"></iframe>');

	// $("#boxright").append('<div class="dk-side"><h3>新版稻壳阅读器上线了</h3><div class="dk-content"><p>十亿文库，免费阅读</p><p>海量文档，极速下载</p></div><a href="http://www.daokeyuedu.com" target="_blank" title="稻壳阅读器" class="dk-btn">下载稻壳阅读器</a></div>');
	// $("#boxright").append('<a class="sidebar-recommended" href="https://reader.doc88.com/" target="_blank"></a>');
	// $("#boxright").append('<div class="adpx250"><iframe style="padding-top:0px;" width="250" src="'+Reader.m_adHost+'bd_250_250_1.html" height="250" frameborder="0" scrolling="no"></iframe></div>');
	var m_sh = screen.height;
	if(m_sh>900)
	{
		//$("#boxright").append('<div class="adpx250"><iframe style="padding-top:0px;" width="250" src="'+Reader.m_adHost+'bd_250_250_2.html" height="250" frameborder="0" scrolling="no"></iframe></div>');
		//Reader.m_bdLoadIf = true;
		// if(m_sh>=1080)
		//$("#boxright").append('<div class="adpx250" style="height:80px;"><iframe style="padding-top:0px;" width="250" src="'+Reader.m_adHost+'bd_250_80_1.html" height="80" frameborder="0" scrolling="no"></iframe></div>');
	}
	else if(m_sh==900)
	{
		//150px;
		//$("#boxright").append('<div class="adpx250" style="height:150px;"><iframe style="padding-top:0px;" width="250" src="'+Reader.m_adHost+'bd_250_150_1.html" height="150" frameborder="0" scrolling="no"></iframe></div>');
	}
	else if(m_sh>=800&&m_sh<900)
	{
		//80px
	   // $("#boxright").append('<div class="adpx250" style="height:80px;"><iframe style="padding-top:0px;" width="250" src="'+Reader.m_adHost+'bd_250_80_1.html" height="80" frameborder="0" scrolling="no"></iframe></div>');
	}
	else if(m_sh>=768&&m_sh<800)
	{
		//50px;
		// $("#boxright").append('<div class="adpx250" style="height:50px;"><iframe style="padding-top:0px;" width="250" src="'+Reader.m_adHost+'bd_250_50_1.html" height="50" frameborder="0" scrolling="no"></iframe></div>');
	}
	Reader.m_adInitIf = true;
	//Reader.m_setListRightPanel();
};
Reader.m_setListRightPanel = function()
{	
	var Y=$(this).scrollTop();
	if(Y>10)
	{
		$(".topshop").slideUp(10);
		$(".skintips").hide();
	}
	if(!m_ie6)
	{
		if(!Reader.m_adInitIf)	
		{
		  return;
		}
		var Y=$(this).scrollTop();
		var m_ph =  $(document).height()-1100;

		if(false)
		{
			if((Y>m_ph/2&&Reader.m_eventPosition==0)||(Y>Reader.m_eventPosition&&Reader.m_eventPosition>0))
			{
			   if(Reader.m_eventPosition>0)
			   {
					if(Y>Reader.m_eventPosition)
					{
						if($('#boxright').css("position")!="fixed"||$("#relatebox").is(":visible"))
						{
							$("#relatebox").hide();
							$(".btndown2").hide();
							$('#box3').hide();
							$('#boxright').css({position:"fixed",left:$("#boxleft").offset().left+$("#boxleft").width()+10,top:"45px"});
						}
			  
						var m_rh = $('#boxright').height();
						var m_ot = $(".activelist").offset().top-11;
						if(Y+m_rh>=m_ot)
						{
							var m_t = -(Y+m_rh-m_ot);
							$('#boxright').css({position:"fixed",left:$("#boxleft").offset().left+$("#boxleft").width()+10,top:m_t+"px"});
						}
						else
						{
						   $('#boxright').css({position:"fixed",left:$("#boxleft").offset().left+$("#boxleft").width()+10,top:"45px"});
						}
					}
			    }
			    else
			    {
				    if($("#relatebox").is(":visible"))
				    {
						Viewer.m_eventPosition = Y;
						$('#boxright').css({position:"absolute",left:$("#boxleft").offset().left+$("#boxleft").width()+10,top:(Y+45)+"px"});
				    }
			    }
			   if(Reader.m_rightLoadMoreIf==0)
			   {
					Reader.m_rightLoadMoreIf = 1;
					if(Reader.m_bdLoadIf)
					{
						$("#boxright").append('<div class="adpx250"><iframe style="padding-top:0px;" width="250" src="'+Reader.m_adHost+'bd_250_250_2.html" height="250" frameborder="0" scrolling="no"></iframe></div>');
					}
					else
					{
						$("#boxright").append('<div class="adpx250"><iframe style="padding-top:0px;" width="250" src="'+Reader.m_adHost+'tb_250_250_1.html" height="250" frameborder="0" scrolling="no"></iframe></div>');
					}
					$("#boxright").append('<div class="adpx250"><iframe style="padding-top:0px;" width="250" src="'+Reader.m_adHost+'bd_250_50_2.html" height="50" frameborder="0" scrolling="no"></iframe></div>');
			   }
			}
			else if(Y<=Reader.m_eventPosition&&Viewer.m_eventPosition>0)
			{
				var m_Y = Y-Reader.m_rightDHeight+(Reader.m_eventPosition-Y);
				if(Y>=Viewer.m_eventPosition-Viewer.m_rightDHeight)
				{
					$('#boxright').css({position:"absolute",left:$("#boxleft").offset().left+$("#boxleft").width()+10,top:(m_Y+45)+"px"});
					if(!$("#relatebox").is(":visible"))
					{
					   $("#relatebox").show();
					   $(".btndown2").show();
					}
				}
				else
				{	
				 
					$("#relatebox").show();
					$(".btndown2").show();
					$('#boxright').css({position:"fixed",left:$("#boxleft").offset().left+$("#boxleft").width()+10,top:"45px"});
			
					if(Y>=Reader.m_rightTopHeight)
					{
						$('#box3').hide();
						var m_rh = $('#boxright').height();
						var m_ot = $(".activelist").offset().top-11;
						if(Y+m_rh>=m_ot)
						{
							var m_t = -(Y+m_rh-m_ot);
							$('#boxright').css({position:"fixed",left:$("#boxleft").offset().left+$("#boxleft").width()+10,top:m_t+"px"});
						}
						else
						{
							$('#boxright').css({position:"fixed",left:$("#boxleft").offset().left+$("#boxleft").width()+10,top:"45px"});
						}
					}
					else if(Y<=50)
					{
					   $('#box3').show();
					   $('#boxright').css({position:"static",left:$("#boxleft").offset().left+$("#boxleft").width()+10,top:"45px"});
					 
					}
				}
			}
			else if(Y>=Reader.m_rightTopHeight)
			{
				$('#box3').hide();
				var m_rh = $('#boxright').height();
				var m_ot = $(".activelist").offset().top-11;;
				if(Y+m_rh>=m_ot)
				{
					var m_t = -(Y+m_rh-m_ot);
					$('#boxright').css({position:"fixed",left:$("#boxleft").offset().left+$("#boxleft").width()+10,top:m_t+"px"});
				}
				else
				{
					$('#boxright').css({position:"fixed",left:$("#boxleft").offset().left+$("#boxleft").width()+10,top:"45px"});
				}
			}
			else if(Y<=50)
			{
			   $('#box3').show();
			   $('#boxright').css({position:"static",left:$("#boxleft").offset().left+$("#boxleft").width()+10,top:"45px"});
			}
		}
		else
		{
			if(Y>=Reader.m_rightTopHeight)
			{
				$('#box3').hide();
				var m_rh = $('#boxright').height();
				var m_ot = $(".activelist").offset().top-11;
				if(Y+m_rh>=m_ot)
				{
					var m_t = -(Y+m_rh-m_ot);
					$('#boxright').css({position:"fixed",left:$("#boxleft").offset().left+$("#boxleft").width()+10,top:m_t+"px"});
				}
				else
				{
					$('#boxright').css({position:"fixed",left:$("#boxleft").offset().left+$("#boxleft").width()+10,top:"10px"});
				}
			}
		}
		Reader.m_lastScrollY = Y;
		if(Y<Reader.m_rightTopHeight&&$('#boxright').css("position")=="fixed")
		{
			$('#box3').show();
			$('#boxright').css({position:"static",left:"0",top:"0"});
		}
		if(Y>50&&$('#readshop').css("position")!="fixed")
		{
			$('#readshop').css({position:"fixed",width:"100%",zIndex:"999"});
		}
		else if(Y<=50&&$('#readshop').css("position")=="fixed")
		{
			$('#readshop').css({position:"static",zIndex:"1"});
		}
	}
	if(m_ie6)
	{
		var Y=$(this).scrollTop();
		if(Y>233)
		{
			$('#box3').hide();
			var m_rh = $('#boxright').height();
			var m_ot = $(".activelist").offset().top-11;
			if(Y+m_rh>=m_ot)
			{
				var m_t = -(Y+m_rh-m_ot);
				$('#boxright').css({position:"absolute",left:$("#boxleft").offset().left+$("#boxleft").width()+10,top:(Y+m_t)+"px"});	
			}
			else
			{
				$('#boxright').css({position:"absolute",left:$("#boxleft").offset().left+$("#boxleft").width()+10,top:(Y+45)+"px"});
			}	
		}
		else
		{ 
		
			var top = 98;
			if(!$(".topshop").is(":hidden"))
			{
				top = 190+98;
			}
			$('#boxright').css({position:"absolute",left:$("#boxleft").offset().left+$("#boxleft").width()+10,top:top+"px"});
			$('#box3').show();
		}
	}
};
function setHomeSearch()
{
	if(typeof(global_page) == "undefined") {
		global_page = "";
	}
	if(global_page=="home")
	{
		if($(window).width()<=990)
		{
            $(".bigsearch .stext").width(200);
            $(".bigsearch .stext").css({'font-size':'12px'});
		}
		else if($(window).width()<=1260)
		{
			$(".bigsearch .stext").width(200);
			$(".bigsearch .stext").css({'font-size':'14px'});
		}
		else
		{
			$(".bigsearch .stext").width(270);
			$(".bigsearch .stext").css({'font-size':'14px'});
		}	
	}
}
function setTopPanel()
{
    if(global_page=="reading")
	{
		var ww = $(window).width();
		var pw = $("#mainPanel").width();   
		var rw = (ww-pw)/2;
		if(rw<0)
		{
			rw = 0;
		}
		rw = rw-74;
		$(".toplayer-shop,.draw-gif").css("right",rw+"px");
	}
}
$(window).resize(function() {
	setHomeSearch();
	setTopPanel();	
});
$(document).ready(function(){   
	setTopPanel();
	setHomeSearch();
	pageInit();
});
function loadScreenCss()
{
	if (typeof(global_page) == "undefined") {
		global_page = "";
	}
	if(global_page!="home"){
		if(global_page=="reading"){
			if (screen.width<=1024) {
				globePageWidth =950;
			} else if (screen.width<=1280) {
				globePageWidth = 1020;
			} else if (screen.width<=1440) {
				globePageWidth = 1150;
			} 
			else if (screen.width<=1680) {
				globePageWidth = 1280;
			}  
			else if (screen.width<=1920) {
				globePageWidth = 1280;
			} 
			else {
				globePageWidth = 1450;
			}
		}
		else{
			if (screen.width<=1024) {
				globePageWidth = 950;
			} else if (screen.width<=1280) {
				globePageWidth = 1020;
			} else if (screen.width<=1440) {
				globePageWidth = 1150;
			} 
			else  
			{
				globePageWidth = 1220;
			}
		}
		loadCss(staticUrl + 'resources/css/response/'+globePageWidth+'.css?v=1.35');
	}
}
loadScreenCss();
function pageInit()
{
	if (typeof(global_page) == "undefined") {
		global_page = "";
	}
	if(global_page!="home"){
		if (screen.width<=1024) {
			Reader.m_listAdArray[0] = Reader.m_adHost+"bd_728_90_9.html";
			Reader.m_listAdArray[1] = Reader.m_adHost+"bd_728_90_10.html";
			// document.write('<link rel="stylesheet" type="text/css" href="' + staticUrl + 'resources/css/response/950.css?v=1.23" />');
		} else if (screen.width<=1280) {
			Reader.m_listAdArray[0] = Reader.m_adHost+"bd_760_90_9.html";
			Reader.m_listAdArray[1] = Reader.m_adHost+"bd_760_90_10.html";
			
		   //document.write('<link rel="stylesheet" type="text/css" href="' + staticUrl + 'resources/css/response/1020.css?v=1.23" />');
		} else if (screen.width<=1440) {
			Reader.m_listAdArray[0] = Reader.m_adHost+"bd_760_90_9.html";
			Reader.m_listAdArray[1] = Reader.m_adHost+"bd_760_90_10.html";
			//document.write('<link rel="stylesheet" type="text/css" href="' + staticUrl + 'resources/css/response/1150.css?v=1.23" />');
		} else if(screen.width<=1680){
			Reader.m_listAdArray[0] = Reader.m_adHost+"bd_960_90_9.html";
			Reader.m_listAdArray[1] = Reader.m_adHost+"bd_960_90_10.html";
			//document.write('<link rel="stylesheet" type="text/css" href="' + staticUrl + 'resources/css/response/1220.css?v=1.23" />');
		}
		
	}
	if(global_page=="home"){
		if (screen.width<=1024) {
			Reader.m_listAdArray[0] = Reader.m_adHost+"bd_728_90_9.html";
			Reader.m_listAdArray[1] = Reader.m_adHost+"bd_728_90_10.html";
			// document.write('<style>.btnupload3{display:none !important;}.mainpart{margin:auto;padding: 0 20px;}.bigsearch .stext{width:140px;padding:0 5px;background-position:left 0;}.commonbox1 .box{padding:10px 0px;margin: 0 30px;}</style>');
		} else if (screen.width<=1280) {
			Reader.m_listAdArray[0] = Reader.m_adHost+"bd_760_90_9.html";
			Reader.m_listAdArray[1] = Reader.m_adHost+"bd_760_90_10.html";
		   //document.write('<style>.btnupload2{display:none !important;}.btnupload1{display:none !important;}.btnupload3{display:block !important;}.mainpart{margin:auto;padding: 0 20px;}.bigsearch .stext{width:140px;padding:0 5px;background-position:left 0;}.commonbox1 .box{padding:10px 0px;margin: 0 30px;}</style>');
		} else if (screen.width<=1440) {
			Reader.m_listAdArray[0] = Reader.m_adHost+"bd_760_90_9.html";
			Reader.m_listAdArray[1] = Reader.m_adHost+"bd_760_90_10.html";
			//globePageWidth = 1150;
			//document.write('<style>.btnupload2{display:none !important;}.btnupload1{display:none !important;}.btnupload3{display:block !important;}.mainpart{margin:auto;padding: 0 20px;}.bigsearch .stext{width:140px;padding:0 5px;background-position:left 0;}.commonbox1 .box{padding:10px 0px;margin: 0 30px;}</style>');
		} else { 
			Reader.m_listAdArray[0] = Reader.m_adHost+"bd_960_90_9.html";
			Reader.m_listAdArray[1] = Reader.m_adHost+"bd_960_90_10.html";
			//globePageWidth = 1220;
			//document.write('<style>.btnupload2{display:none !important;}.btnupload3{display:none !important;}.btnupload1{display:block !important;}.mainpart{margin: auto;padding: 0 20px;}.bigsearch .stext{font: 14px/1.5 "Microsoft YaHei","微软雅黑","SimSun","宋体";width:310px;padding:0 5px;background-position:left 0;}.commonbox1 .box{padding:10px 0px;margin: 0 30px;}</style>');
		}
	}
    Reader.m_listAdArray[0] = Reader.m_adHost+"doc88_960_90_1.html";
	Reader.m_listAdArray[1] = Reader.m_adHost+"doc88_960_90_1.html";
	if(global_page=="reading")
	{
		var m_saveBg = false;
		var m_bgtype = getCookie("BG_TYPE");
		if(m_bgtype==""||m_bgtype==0)
		{
			var m_bgimg = getCookie("BG_IMG");
			if(m_bgimg=="")
			{
				m_bgimg  =staticUrl+"assets/images/skin/skin-paper1-img.png";
				// m_bgimg = staticUrl+"/assets/images/skin/0701/skin-0701-"+globePageWidth+".jpg";	
				//m_bgimg = staticUrl+"/assets/images/skin/festival/skin-festival-lantern-"+globePageWidth+".png";
			}
			else
			{
				m_saveBg = true;
			}
			var m_bgcolor = getCookie("BG_COLOR");
			var m_img_type = getCookie("BG_IMG_TYPE");
			if(m_img_type=="")
			{
				m_img_type = 0;
			}
		
			if(m_img_type==1)
			{
				var m_bgcolor = getCookie("BG_COLOR");
				if(m_bgcolor=="")
				{
					m_bgcolor = "#fbf4f0";    
					//m_bgcolor= "#de1a17";
				}
				document.body.style.cssText = 'background:'+m_bgcolor+' url('+m_bgimg+') no-repeat center top;background-attachment:fixed;';
				$("#header").css("background","rgba(0,0,0,0.5)");
			}
			else
			{
				document.body.style.cssText = 'background:url('+m_bgimg+') repeat;background-attachment:fixed;';
			}
		}
		else if(m_bgtype==1)
		{
			m_saveBg = true;
			var m_bgcolor = getCookie("BG_COLOR");
			document.body.style.cssText = 'background:'+m_bgcolor+' repeat;background-attachment:fixed;';
		}
		
		if(m_saveBg)
		{
			var bg_save = getCookie("BG_SAVE");
			if(bg_save!=1)
			{
				var bc = getCookie("BG_COLOR");
				if(bc==undefined||bc=="undefined")
				{
					bc = "";
				}
				var bid = getCookie("BG_ID");
				if(bid==undefined||bid=="undefined")
				{
					bid = "";
				}
				setCookie("BG_SAVE",1,30*24);
				$.ajax({
					url: '/index.php?act=s_skin',
					type: 'post',
					data: {
						type: m_bgtype,
						id:bid,
						color:bc
					},
					dataType: 'json',
					success: function(msg){
						
					}
				});
			}
		}
	}
	else
	{
		if(global_page!="")
		{
			document.body.style.cssText = 'background:url('+staticUrl+'assets/images/skin/skin-paper1.png) repeat;background-attachment:fixed;';
		}
	}
	if(global_page=="list")
	{
		if(!IsPC())
		{
			//document.write('<style>.layout02 .boxleft{margin-left:20px;margin-right:20px!important;} .layout02 .boxright{display:none!important}</style>');
		}
	}
}
function showTipWin(tip)
{
	DOC88Window.win({message: '/js/home/window.tip.html?tip='+encodeURIComponent(tip),width:300,height:180,title:'提示信息',iframe:true});	
}
function showTipsWin(tip)
{
	DOC88Window.win({message: '/js/home/window_reading_tip.html?&tip='+encodeURIComponent(tip),width:600,height:230,title:'提示信息',iframe:true});	
}

function isIE7()
{
    var browser=navigator.appName;
    if(browser=="Microsoft Internet Explorer")
    {
        var b_version=navigator.appVersion;
        var version=b_version.split(";");
        var trim_Version=version[1].replace(/[ ]/g,"");
        if(trim_Version=="MSIE7.0")
        {
            return true;
        }
    }
    return false;
}
function isIE6()
{
    var browser=navigator.appName;
    if(browser=="Microsoft Internet Explorer")
    {
        var b_version=navigator.appVersion;
        var version=b_version.split(";");
        var trim_Version=version[1].replace(/[ ]/g,"");
        if(trim_Version=="MSIE6.0")
        {
            return true;
        }
    }
    return false;
}
//主导航子菜单
$(document).ready(function(){
	$(".mainnav li.dropdown").mousemove(function(){
		if($(this).find(".dorpmenu1,.dorpmenu2").is(":visible"))
		{
			return;
		}
		if(isIE7()||isIE6())
		{
			$(this).find(".dorpmenu2").show();
		}
		else
		{
			$(this).find(".dorpmenu2").slideDown("fast");
		}
	});
	$(".mainnav li.dropdown").mouseleave(function(){
		if(isIE7()||isIE6())
		{
			$(this).find(".dorpmenu1,.dorpmenu2").hide();
		}
		else
		{
			$(this).find(".dorpmenu1,.dorpmenu2").slideUp("fast");
		}
	})
});
var JPlaceHolder = {
    _check : function(){
        return 'placeholder' in document.createElement('input');
    },
    init : function(){
        if(!this._check()){
            this.fix();
        }
    },
    fix : function(){
        jQuery(':input[placeholder]').each(function(index, element) {
            var self = $(this), txt = self.attr('placeholder');
            self.wrap($('<div></div>').css({position:'relative', zoom:'1', border:'none', background:'none', padding:'none', margin:'none'}));
            var pos = self.position(), h = self.outerHeight(true), paddingleft = self.css('padding-left');
            var holder = $('<span></span>').text(txt).css({position:'absolute', left:pos.left, top:pos.top, height:h, lineHeight:h+'px', paddingLeft:paddingleft, color:'#aaa'}).appendTo(self.parent());
            self.focusin(function(e) {
                holder.hide();
            }).focusout(function(e) {
                if(!self.val()){
                    holder.show();
                }
            });
            holder.click(function(e) {
                holder.hide();
                self.focus();
            });
			var txt = self.attr('value');
			if(txt!="")
			{
				holder.hide();
			}
		});
    }
};
jQuery(function(){
    if(!isIE6())
    {
		JPlaceHolder.init();    
    }
});
