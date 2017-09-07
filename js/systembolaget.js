var products = {}
var info = {}

const loadData = () => {
    $.get({
        url: 'products/5.json'
    }).done(ps => {
        products = ps
    })

    $.get({
        url: 'info.json'
    }).done(data => info = data)
}

const getStores = () => {
    var selects = [document.getElementById('store1'), document.getElementById('store2')]

    $.get({
        url: 'stores/info.json',
        contentType: 'json'
    }).done(stores => {
        stores.forEach(store => {
            const [nr, name, city] = store
            
            selects.forEach(select => {
                var option = document.createElement('option')
                option.value = nr
                option.text = `${city} - ${name}`
                select.appendChild(option)
            })
        })
    })
}

const addEventListener = () => {
    document.getElementById('compare').addEventListener('click', getStoreStock)
}

var storeStock = []

const getStoreStock = event => {
    const selectedStores = [
        parseInt(document.getElementById('store1').value),
        parseInt(document.getElementById('store2').value)
    ]
    storeStock = []
    selectedStores.forEach(store => getStock(store))
}

Array.prototype.diff = a => {
    return this.filter(i => a.indexOf(i) < 0)
}

var storeDiffStock = []

const getProductInformation = ids => {
    var stores = []
    
    ids.forEach(diff => {
        var store = []
        diff.forEach(id => store.push(products[id]))
        stores.push(store)
    })
    viewProductDiff(stores)
}

const viewProductDiff = stores => {
    const store1 = document.getElementById('store1Result')
    const store2 = document.getElementById('store2Result')

    while (store1.hasChildNodes())
        store1.removeChild(store1.lastChild)

    while (store2.hasChildNodes())
        store2.removeChild(store2.lastChild)

    stores[0].forEach(product => addProduct(product, store1))
    stores[1].forEach(product => addProduct(product, store2))
}

const addProduct = (product, elem) => {
    const p = document.createElement('div')
    p.classList.add('col-sm-4')

    const p2 = document.createElement('div')
    p2.classList.add('product')

    const [name, name2, price, url, country, format, volume, style, type] = product

    const link = document.createElement('a')
    link.href = `https://systembolaget.se/dryck/${url}`

    const pName = document.createElement('div')
    pName.classList.add('product-name')
    pName.innerText += name

    const pText = document.createElement('div')
    pText.classList.add('product-text')
    pText.innerHTML += country && `${info.countries[country]}<br />`
    pText.innerHTML += style && `${info.styles[style]}<br />`
    pText.innerHTML += type && `${info.types[type]}`

    link.appendChild(pName)
    link.appendChild(pText)

    p2.appendChild(link)
    p.appendChild(p2)

    elem.appendChild(p)
}

const compareStore = () => {
    const categories = [storeStock[0][5], storeStock[1][5]]
    const diff = categories.map((c,i,t) => {
        const flat = t.filter(y => y !== c).reduce((a, z) => a.concat(z), [])
        return c.filter(n => flat.filter(g => g === n).length<t.length-1)
    })
    getProductInformation(diff)
}

const addStock = stock => {
    storeStock.push(stock)
    if (storeStock.length === 2)
        compareStore()
}

const getStock = storeId => {
    $.get({
        url: `stores/${storeId}.json`,
        aync: false,
        success: addStock
    })
}

loadData()
getStores()
addEventListener()