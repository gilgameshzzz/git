# Filename  : middleware.py
# Date  : 2018/9/28
import re

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin

from cart.models import ShoppingCart
from users.models import User


class UserAuthMiddleware(MiddlewareMixin):
	def process_request(self, request):
		# 登录验证中间件
		# 不需要登录验证的URL地址
		not_need_check = ['/users/index/', '/users/login/', '/users/register/'
		                  , '/cart/(.*)/', '/media/(.*)/', '/static/(.*)/',
		                  '/goods/goods_detail/(\d+)/', '/base/']
		path = request.path
		for not_path in not_need_check:
			# 匹配当前URL地址是不是不需要登录验证
			if re.match(not_path, path):
				return None

		# 登录验证开始
		user_id = request.session.get('user_id')
		# 没有登录，获取不到user_id参数，则跳转到登录页面
		if not user_id:
			return HttpResponseRedirect(reverse('users:login'))

		# 给request.user赋值，赋值为当前登录系统的用户
		user = User.objects.get(pk=user_id)
		request.user = user

		return None


class UserSessionMiddleware(MiddlewareMixin):
	# 同步session数据到shopping_cart表
	def process_request(self, request):
		user_id = request.session.get('user_id')
		if user_id:
			# 获取到session中的商品数据
			session_goods = request.session.get('goods')
			if session_goods:
				# 1、如果购物车中没有session中的商品数据，则创建
				# 2、如果购物车中有session中的商品数据，则更新
				# session中商品信息的结构[[id,num,is_select],[id,num,is_select]]
				for goods in session_goods:
					# 查询购物车是否存在商品信息
					cart = ShoppingCart.objects.filter(goods_id=goods[0],
					                                   user_id=user_id).first()
					if cart:
						if cart.nums != goods[1]:
							# 如果商品数量不相同，则同步商品数量
							cart.nums = int(goods[1])
						# 	同步商品选择状态
						cart.is_select = int(goods[2])
						cart.save()
					else:
						# session中的商品数据不存在与购物车中，则保存
						ShoppingCart.objects.create(
							user_id=user_id,
							goods_id=goods[0],
							nums=int(goods[1]),
							is_select=int(goods[2])
						)