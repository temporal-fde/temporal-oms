<script lang="ts">
	import type { PageData } from './$types';

	export let data: PageData;

	function formatPrice(priceCents: number): string {
		return `$${(priceCents / 100).toFixed(2)}`;
	}

	function formatDate(dateString: string): string {
		return new Date(dateString).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'long',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function getStatusColor(status: string): string {
		const colors: Record<string, string> = {
			pending: 'bg-yellow-100 text-yellow-800',
			processing: 'bg-blue-100 text-blue-800',
			completed: 'bg-green-100 text-green-800',
			cancelled: 'bg-red-100 text-red-800',
			failed: 'bg-red-100 text-red-800'
		};
		return colors[status] || 'bg-gray-100 text-gray-800';
	}
</script>

<svelte:head>
	<title>My Orders - Temporal OMS</title>
</svelte:head>

<div class="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
	<div class="mb-8">
		<h1 class="text-3xl font-bold text-gray-900">My Orders</h1>
		<p class="mt-2 text-gray-600">Customer ID: {data.customerId}</p>
	</div>

	{#if data.orders.length === 0}
		<div class="bg-white rounded-lg shadow-md p-12 text-center">
			<svg
				class="w-16 h-16 text-gray-400 mx-auto mb-4"
				fill="none"
				stroke="currentColor"
				viewBox="0 0 24 24"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
				/>
			</svg>
			<h2 class="text-xl font-semibold text-gray-900 mb-2">No orders yet</h2>
			<p class="text-gray-600 mb-6">Start shopping to see your orders here</p>
			<a
				href="/shop/home"
				class="inline-flex items-center bg-primary-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-primary-700 transition-colors"
			>
				Start Shopping
			</a>
		</div>
	{:else}
		<div class="space-y-6">
			{#each data.orders as order}
				<div class="bg-white rounded-lg shadow-md overflow-hidden">
					<!-- Order Header -->
					<div class="bg-gray-50 px-6 py-4 border-b border-gray-200">
						<div class="flex flex-wrap items-center justify-between gap-4">
							<div>
								<div class="flex items-center space-x-4">
									<h3 class="text-lg font-semibold text-gray-900">
										Order #{order.orderId}
									</h3>
									<span class="px-3 py-1 rounded-full text-sm font-medium {getStatusColor(order.status)}">
										{order.status.toUpperCase()}
									</span>
								</div>
								<p class="text-sm text-gray-600 mt-1">
									Placed on {formatDate(order.createdAt)}
								</p>
							</div>
							<div class="text-right">
								<div class="text-2xl font-bold text-gray-900">
									{formatPrice(order.totalCents)}
								</div>
								<p class="text-sm text-gray-600">{order.items.length} items</p>
							</div>
						</div>
					</div>

					<!-- Order Items -->
					<div class="px-6 py-4">
						<div class="space-y-3">
							{#each order.items as item}
								<div class="flex items-center space-x-4">
									<div class="w-16 h-16 bg-gradient-to-br from-gray-100 to-gray-200 rounded flex items-center justify-center flex-shrink-0">
										<svg
											class="w-8 h-8 text-gray-400"
											fill="none"
											stroke="currentColor"
											viewBox="0 0 24 24"
										>
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												stroke-width="1.5"
												d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"
											/>
										</svg>
									</div>
									<div class="flex-1 min-w-0">
										<p class="font-medium text-gray-900">{item.name}</p>
										<p class="text-sm text-gray-600">Quantity: {item.quantity}</p>
									</div>
									<div class="text-right">
										<p class="font-medium text-gray-900">{formatPrice(item.priceCents)}</p>
									</div>
								</div>
							{/each}
						</div>
					</div>

					<!-- Shipping Address (if available) -->
					{#if order.shippingAddress}
						<div class="px-6 py-4 bg-gray-50 border-t border-gray-200">
							<h4 class="text-sm font-semibold text-gray-900 mb-2">Shipping Address</h4>
							<p class="text-sm text-gray-600">
								{order.shippingAddress.street}<br />
								{order.shippingAddress.city}, {order.shippingAddress.state} {order.shippingAddress.postalCode}<br />
								{order.shippingAddress.country}
							</p>
						</div>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</div>
